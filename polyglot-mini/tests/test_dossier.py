from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from polyglot.dossier import generate_dossier, replay_dossier, verify_patch_authority


class DossierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        (self.root / "docs" / "decisions").mkdir(parents=True)
        (self.root / "polyglot").mkdir(parents=True)
        (self.root / "packages").mkdir(parents=True)
        (self.root / "specs").mkdir(parents=True)

        (self.root / "docs" / "decisions" / "DEC-0001-dossier-provider-boundary.md").write_text(
            "# DEC-0001 Dossier provider boundary\n\n"
            "## Decision\n\n"
            "Implementation authority must come from verified local sources or promoted decisions.\n"
        )
        (self.root / "docs" / "decisions" / "DEC-0001-dossier-provider-boundary.scope.json").write_text(
            json.dumps(
                {
                    "decisionId": "DEC-0001",
                    "level": "A",
                    "status": "current_hard_gate",
                    "allowedPaths": ["polyglot/*.py", "docs/decisions/*", "specs/*.md"],
                    "forbiddenPaths": ["packages/*"],
                    "forbiddenImports": ["notebooklm", "notebooklm_py"],
                    "forbiddenStrings": ["design_inference"],
                    "symbolAccounting": {
                        "required": True,
                        "language": "python",
                        "topLevelKinds": ["function", "class", "import"],
                        "mode": "added_or_modified",
                    },
                    "forbiddenCapabilities": [
                        {
                            "name": "network_access",
                            "pythonImports": ["requests", "httpx", "aiohttp", "socket", "urllib.request"],
                            "pythonCalls": [
                                "requests.get",
                                "requests.post",
                                "httpx.get",
                                "httpx.post",
                                "urllib.request.urlopen",
                                "socket.socket",
                            ],
                        }
                    ],
                },
                indent=2,
            )
        )
        (self.root / "polyglot" / "cli.py").write_text('"""CLI entry."""\n\ndef main():\n    return 0\n')
        (self.root / "polyglot" / "dossier.py").write_text('ALLOWED = True\n')
        (self.root / "polyglot" / "extra.py").write_text('EXTRA = True\n')
        (self.root / "packages" / "other.ts").write_text('export const other = true;\n')
        (self.root / "specs" / "task.md").write_text(
            "Implement the local dossier provider and authority gate.\n"
            "planner-context.md may include design_inference.\n"
            "executor-context.md must exclude raw design_inference text.\n"
        )

        self._git("init")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test User")
        self._git("add", ".")
        self._git("commit", "-m", "base")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            text=True,
            capture_output=True,
        )

    def _generate(self) -> dict:
        out_path = self.root / "exports" / "executor-context.md"
        return generate_dossier(
            task="Implement the local dossier provider and authority gate.",
            provider="local",
            sources=[
                str(self.root / "specs" / "task.md"),
                str(self.root / "polyglot"),
                str(self.root / "docs" / "decisions"),
            ],
            out_path=str(out_path),
            working_dir=str(self.root),
        )

    def _ledger(self, run_dir: Path) -> dict:
        return json.loads((run_dir / "claim-ledger.json").read_text())

    def _write_patch_ledger(self, run_dir: Path, result: dict, changes: list[dict]) -> Path:
        patch_ledger = {
            "baseSourceSnapshot": result["base_source_snapshot"],
            "baseGitSha": result.get("base_git_sha"),
            "changes": changes,
        }
        path = run_dir / "patch-ledger.json"
        path.write_text(json.dumps(patch_ledger, indent=2))
        return path

    def test_claim_ledger_generation_writes_artifacts(self) -> None:
        result = self._generate()
        self.assertTrue(result["ok"], result)
        run_dir = Path(result["run_dir"])

        self.assertTrue((run_dir / "source-ledger.json").exists())
        self.assertTrue((run_dir / "claim-ledger.json").exists())
        self.assertTrue((run_dir / "codex-context-pack.json").exists())
        self.assertTrue((run_dir / "planner-context.md").exists())
        self.assertTrue((run_dir / "executor-context.md").exists())
        self.assertTrue((run_dir / "manifest.json").exists())

        ledger = self._ledger(run_dir)
        authority_classes = {claim["authorityClass"] for claim in ledger["claims"]}
        self.assertIn("implementation_fact", authority_classes)
        self.assertIn("promoted_decision", authority_classes)
        self.assertIn("planning_inference", authority_classes)
        self.assertIn("execution_verified_fact", authority_classes)

    def test_notebooklm_provider_is_structured_unavailable_seam(self) -> None:
        result = generate_dossier(
            task="Try the volatile provider seam.",
            provider="notebooklm",
            sources=[str(self.root / "specs" / "task.md")],
            out_path=str(self.root / "exports" / "notebooklm.md"),
            working_dir=str(self.root),
        )

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "NOT_IMPLEMENTED")
        self.assertEqual(result["error"]["details"]["provider"], "notebooklm")
        manifest = json.loads((Path(result["manifest_path"])).read_text())
        self.assertFalse(manifest["ok"], manifest)
        self.assertEqual(manifest["notebooklm"]["status"], "not_implemented")

    def test_executor_filtering_excludes_design_inference(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        planner_text = (run_dir / "planner-context.md").read_text()
        executor_text = (run_dir / "executor-context.md").read_text()

        self.assertIn("design_inference", planner_text)
        self.assertNotIn("design_inference", executor_text)
        self.assertNotIn("Prefer implementing inside the existing CLI surface", executor_text)
        self.assertIn("promoted_decisions", executor_text)

    def test_offline_replay_regenerates_context(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        expected_executor = (run_dir / "executor-context.md").read_text()
        replay_out = self.root / "replayed" / "executor-context.md"

        replay = replay_dossier(str(run_dir), out_path=str(replay_out))
        self.assertTrue(replay["ok"], replay)
        self.assertEqual(replay_out.read_text(), expected_executor)

    def test_level_a_gate_rejects_forbidden_path(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "packages" / "other.ts").write_text('export const other = false;\n')
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "packages/other.ts",
                    "hunks": [
                        {
                            "hunkId": "HUNK-001",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_nested_path_that_allowed_glob_does_not_cover(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "nested").mkdir()
        (self.root / "polyglot" / "nested" / "hidden.py").write_text("NESTED = True\n")
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/nested/hidden.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-001B",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_nested_forbidden_path(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "packages" / "nested").mkdir()
        (self.root / "packages" / "nested" / "other.ts").write_text("export const nested = true;\n")
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "packages/nested/other.ts",
                    "hunks": [
                        {
                            "hunkId": "HUNK-001C",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_forbidden_import_or_string(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "dossier.py").write_text('import notebooklm\nDESIGN = "design_inference"\n')
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-002",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_forbidden_capability(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "dossier.py").write_text(
            "import requests\n\n"
            "def fetch_remote_status():\n"
            '    return requests.get("https://example.com/status").status_code\n'
        )
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "symbols": [
                        {"kind": "import", "name": "requests"},
                        {"kind": "function", "name": "fetch_remote_status"},
                    ],
                    "hunks": [
                        {
                            "hunkId": "HUNK-002B",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_unaccounted_file(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "dossier.py").write_text('ALLOWED = False\n')
        (self.root / "polyglot" / "extra.py").write_text('EXTRA = False\n')
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-003",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_unaccounted_changed_python_symbol(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "dossier.py").write_text(
            "ALLOWED = True\n\n"
            "def add_authority_gate() -> bool:\n"
            "    return True\n"
        )
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-003B",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_SCOPE_VIOLATION")

    def test_level_a_gate_rejects_tainted_claim(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        planning_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "planning_inference")

        (self.root / "polyglot" / "dossier.py").write_text('ALLOWED = False\n')
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-004",
                            "claimIds": [planning_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertFalse(verification["ok"], verification)
        self.assertEqual(verification["error"]["code"], "PATCH_AUTHORITY_DENIED")

    def test_level_a_gate_accepts_minimal_safe_patch_and_emits_certificate(self) -> None:
        result = self._generate()
        run_dir = Path(result["run_dir"])
        ledger = self._ledger(run_dir)
        impl_claim = next(claim for claim in ledger["claims"] if claim["authorityClass"] == "implementation_fact")

        (self.root / "polyglot" / "dossier.py").write_text('ALLOWED = False\n')
        self._write_patch_ledger(
            run_dir,
            result,
            changes=[
                {
                    "file": "polyglot/dossier.py",
                    "hunks": [
                        {
                            "hunkId": "HUNK-005",
                            "claimIds": [impl_claim["claimId"]],
                            "decisionIds": ["DEC-0001"],
                        }
                    ],
                }
            ],
        )

        verification = verify_patch_authority(run_dir=str(run_dir), repository_root=str(self.root))
        self.assertTrue(verification["ok"], verification)
        certificate = json.loads((run_dir / "scope-certificate.json").read_text())
        self.assertTrue(certificate["ok"], certificate)
        self.assertEqual(certificate["decisionIds"], ["DEC-0001"])


if __name__ == "__main__":
    unittest.main()
