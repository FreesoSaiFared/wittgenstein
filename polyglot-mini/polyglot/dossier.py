from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .notebooklm_adapter import (
    CONTRACT_VERSION as NOTEBOOKLM_PROVIDER_RESULT_CONTRACT_VERSION,
    build_notebooklm_provider_request,
    run_notebooklm_provider_adapter,
)
from .notebooklm_provider import preflight_notebooklm_provider
from .notebooklm_promotion_policy import evaluate_notebooklm_provider_promotion

TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ts",
    ".tsx",
    ".js",
    ".cjs",
    ".mjs",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
ALLOWED_EXECUTOR_AUTHORITY = {
    "implementation_fact",
    "execution_verified_fact",
    "promoted_decision",
}
DENIED_IMPLEMENTATION_STATUSES = {"unverified", "contradicted", "source_missing", "partially_verified"}
STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "from",
    "this",
    "into",
    "must",
    "only",
    "then",
    "than",
    "have",
    "will",
    "need",
    "your",
    "local",
    "provider",
    "context",
    "dossier",
    "claim",
    "patch",
    "authority",
    "implement",
}
FORBIDDEN_PLANNING_MARKERS = ("design_inference", "planning_inference")


class DossierError(Exception):
    def __init__(self, code: str, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_error(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def generate_dossier(
    task: str,
    *,
    provider: str,
    sources: list[str],
    out_path: str,
    working_dir: str | None = None,
    run_id: str | None = None,
    max_files: int = 8,
) -> dict:
    started = time.time()
    cwd = Path(working_dir or os.getcwd()).resolve()
    workspace_root = _find_workspace_root(cwd)
    run_id = run_id or _new_run_id()
    run_dir = workspace_root / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    requested_out = Path(out_path)
    if not requested_out.is_absolute():
        requested_out = (cwd / requested_out).resolve()
    requested_out.parent.mkdir(parents=True, exist_ok=True)

    provider_metadata = _resolve_provider_metadata(provider)
    if provider == "notebooklm":
        provider_request = build_notebooklm_provider_request(
            task=task,
            run_id=run_id,
            workspace_root=workspace_root,
            working_directory=cwd,
            base_git_sha=None,
            base_source_snapshot=None,
            source_ledger_path=run_dir / "source-ledger.json",
            claim_ledger_path=run_dir / "claim-ledger.json",
            requested_out_path=requested_out,
        )
        preflight_metadata = json.loads(json.dumps(provider_metadata, sort_keys=True))
        adapter_result = run_notebooklm_provider_adapter(
            request=provider_request,
            preflight=preflight_metadata,
        )
        provider_metadata["contractVersion"] = NOTEBOOKLM_PROVIDER_RESULT_CONTRACT_VERSION
        provider_metadata["adapterResult"] = adapter_result
        provider_metadata["adapterStatus"] = adapter_result.get("status")
        promotion_decision = evaluate_notebooklm_provider_promotion(
            adapter_result,
            target="executor_context",
        )
        provider_metadata["promotionDecision"] = promotion_decision
        provider_metadata["plannerOnlyUntilLocalPromotion"] = not promotion_decision.get(
            "canEnterExecutorContext",
            False,
        )
    provider_error = _provider_error(provider_metadata)
    provider_output_path = run_dir / "provider-output.md"

    if provider_error is not None:
        return _write_failed_manifest(
            run_dir=run_dir,
            task=task,
            provider=provider,
            provider_metadata=provider_metadata,
            provider_output_path=provider_output_path,
            out_path=str(requested_out),
            workspace_root=workspace_root,
            working_dir=cwd,
            started=started,
            error=provider_error,
        )

    source_ledger = _build_source_ledger(task=task, sources=sources, cwd=cwd, max_files=max_files)
    claims = _build_claims(task=task, source_ledger=source_ledger)
    decisions = _build_decisions(source_ledger=source_ledger, claims=claims, repo_root=workspace_root)
    patch_template = {
        "baseSourceSnapshot": source_ledger["baseSourceSnapshot"],
        "baseGitSha": source_ledger.get("baseGitSha"),
        "changes": [],
    }
    context_pack = _build_context_pack(
        task=task,
        provider=provider,
        run_id=run_id,
        provider_metadata=provider_metadata,
        source_ledger=source_ledger,
        claims=claims,
        decisions=decisions,
        workspace_root=workspace_root,
    )
    provider_output = _render_provider_output(
        task=task,
        provider=provider,
        provider_metadata=provider_metadata,
        source_ledger=source_ledger,
        claims=claims,
    )
    planner_context = _render_planner_context(task=task, context_pack=context_pack, claims=claims)
    executor_context = _render_executor_context(task=task, context_pack=context_pack, claims=claims)

    _write_json(run_dir / "source-ledger.json", source_ledger)
    _write_json(run_dir / "claim-ledger.json", {"claims": claims})
    _write_json(run_dir / "codex-context-pack.json", context_pack)
    _write_json(run_dir / "patch-ledger.json", patch_template)
    provider_output_path.write_text(provider_output)
    (run_dir / "planner-context.md").write_text(planner_context)
    (run_dir / "executor-context.md").write_text(executor_context)
    shutil.copyfile(run_dir / "executor-context.md", requested_out)

    duration_ms = int((time.time() - started) * 1000)
    manifest = {
        "runId": run_id,
        "task": task,
        "provider": provider,
        "providerMetadata": provider_metadata,
        "providerMeta": provider_metadata,
        "workspaceRoot": str(workspace_root),
        "workingDirectory": str(cwd),
        "baseGitSha": source_ledger.get("baseGitSha"),
        "baseSourceSnapshot": source_ledger["baseSourceSnapshot"],
        "requestedOutPath": str(requested_out),
        "artifactPath": str(run_dir / "executor-context.md"),
        "providerOutputPath": str(provider_output_path),
        "plannerContextPath": str(run_dir / "planner-context.md"),
        "contextPackPath": str(run_dir / "codex-context-pack.json"),
        "claimLedgerPath": str(run_dir / "claim-ledger.json"),
        "sourceLedgerPath": str(run_dir / "source-ledger.json"),
        "patchLedgerPath": str(run_dir / "patch-ledger.json"),
        "startedAt": _utc_now(),
        "durationMs": duration_ms,
        "ok": True,
        "error": None,
        "notebooklm": _legacy_notebooklm_status(provider_metadata),
    }
    _write_json(run_dir / "manifest.json", manifest)
    return {
        "ok": True,
        "provider": provider,
        "run_dir": str(run_dir),
        "out_path": str(requested_out),
        "base_source_snapshot": source_ledger["baseSourceSnapshot"],
        "base_git_sha": source_ledger.get("baseGitSha"),
        "manifest_path": str(run_dir / "manifest.json"),
        "provider_output_path": str(provider_output_path),
        "artifact_path": str(run_dir / "executor-context.md"),
        "planner_context_path": str(run_dir / "planner-context.md"),
        "executor_context_path": str(run_dir / "executor-context.md"),
        "provider_meta": provider_metadata,
        "error": None,
    }

def replay_dossier(run_dir: str, *, out_path: str | None = None) -> dict:
    run_path = Path(run_dir).resolve()
    manifest = json.loads((run_path / "manifest.json").read_text())
    claims = json.loads((run_path / "claim-ledger.json").read_text())["claims"]
    context_pack = json.loads((run_path / "codex-context-pack.json").read_text())
    task = manifest["task"]

    planner_context = _render_planner_context(task=task, context_pack=context_pack, claims=claims)
    executor_context = _render_executor_context(task=task, context_pack=context_pack, claims=claims)
    (run_path / "planner-context.md").write_text(planner_context)
    (run_path / "executor-context.md").write_text(executor_context)

    if out_path:
        requested_out = Path(out_path)
        if not requested_out.is_absolute():
            requested_out = (Path(manifest["workingDirectory"]) / requested_out).resolve()
        requested_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(run_path / "executor-context.md", requested_out)
    else:
        requested_out = run_path / "executor-context.md"

    return {
        "ok": True,
        "run_dir": str(run_path),
        "out_path": str(requested_out),
        "artifact_path": str(run_path / "executor-context.md"),
    }


def verify_patch_authority(
    *,
    run_dir: str,
    patch_ledger_path: str | None = None,
    repository_root: str | None = None,
) -> dict:
    run_path = Path(run_dir).resolve()
    manifest = json.loads((run_path / "manifest.json").read_text())
    context_pack = json.loads((run_path / "codex-context-pack.json").read_text())
    source_ledger = json.loads((run_path / "source-ledger.json").read_text())
    claim_ledger = json.loads((run_path / "claim-ledger.json").read_text())["claims"]
    patch_path = Path(patch_ledger_path).resolve() if patch_ledger_path else run_path / "patch-ledger.json"
    patch_ledger = json.loads(patch_path.read_text())
    repo_root = Path(repository_root or context_pack["workspaceRoot"]).resolve()

    authority_violations: list[dict] = []
    scope_violations: list[dict] = []
    python_symbol_changes: list[dict] = []
    decision_ids = sorted({
        decision_id
        for change in patch_ledger.get("changes", [])
        for hunk in change.get("hunks", [])
        for decision_id in hunk.get("decisionIds", [])
    })
    ignored_paths = _ignored_diff_paths(repo_root=repo_root, run_path=run_path, manifest=manifest)
    changed_files = [path for path in _git_changed_files(repo_root) if path not in ignored_paths]
    accounted_files = {change["file"] for change in patch_ledger.get("changes", [])}

    expected_snapshot = context_pack["baseSourceSnapshot"]
    expected_git = context_pack.get("baseGitSha")
    if patch_ledger.get("baseSourceSnapshot") != expected_snapshot:
        scope_violations.append(
            {
                "reason": "patch_ledger_base_mismatch",
                "expected": expected_snapshot,
                "actual": patch_ledger.get("baseSourceSnapshot"),
            }
        )
    if patch_ledger.get("baseGitSha") != expected_git:
        scope_violations.append(
            {
                "reason": "patch_ledger_git_base_mismatch",
                "expected": expected_git,
                "actual": patch_ledger.get("baseGitSha"),
            }
        )

    current_git = _git_sha(repo_root)
    if expected_git and current_git and current_git != expected_git:
        scope_violations.append(
            {
                "reason": "head_mismatch",
                "expected": expected_git,
                "actual": current_git,
            }
        )

    head_snapshot = _compute_head_snapshot(source_ledger, repo_root)
    if head_snapshot != expected_snapshot:
        scope_violations.append(
            {
                "reason": "source_snapshot_mismatch",
                "expected": expected_snapshot,
                "actual": head_snapshot,
            }
        )

    for changed_file in changed_files:
        if changed_file not in accounted_files:
            scope_violations.append(
                {
                    "reason": "unaccounted_file",
                    "file": changed_file,
                }
            )

    claim_index = {claim["claimId"]: claim for claim in claim_ledger}
    decision_index = {decision["decisionId"]: decision for decision in context_pack.get("decisions", [])}

    for change in patch_ledger.get("changes", []):
        file_path = change["file"]
        file_scopes: list[dict] = []
        cited_claims: list[dict] = []
        for hunk in change.get("hunks", []):
            claim_ids = hunk.get("claimIds", [])
            cited_decisions = hunk.get("decisionIds", [])
            if not claim_ids and not cited_decisions:
                authority_violations.append(
                    {"file": file_path, "hunkId": hunk.get("hunkId"), "reason": "missing_authority_citation"}
                )
            for claim_id in claim_ids:
                claim = claim_index.get(claim_id)
                if not claim:
                    authority_violations.append(
                        {"file": file_path, "hunkId": hunk.get("hunkId"), "claimId": claim_id, "reason": "unknown_claim"}
                    )
                    continue
                cited_claims.append(claim)
                if claim["authorityClass"] not in ALLOWED_EXECUTOR_AUTHORITY:
                    authority_violations.append(
                        {
                            "file": file_path,
                            "hunkId": hunk.get("hunkId"),
                            "claimId": claim_id,
                            "reason": "authority_class_not_implementation_safe",
                            "authorityClass": claim["authorityClass"],
                        }
                    )
                elif claim["status"] in DENIED_IMPLEMENTATION_STATUSES:
                    authority_violations.append(
                        {
                            "file": file_path,
                            "hunkId": hunk.get("hunkId"),
                            "claimId": claim_id,
                            "reason": "claim_status_not_implementation_safe",
                            "status": claim["status"],
                        }
                    )
                elif "implementation" not in claim.get("allowedUse", []):
                    authority_violations.append(
                        {
                            "file": file_path,
                            "hunkId": hunk.get("hunkId"),
                            "claimId": claim_id,
                            "reason": "claim_not_allowed_for_implementation",
                        }
                    )
            for decision_id in cited_decisions:
                decision = decision_index.get(decision_id)
                if not decision:
                    scope_violations.append(
                        {"file": file_path, "hunkId": hunk.get("hunkId"), "decisionId": decision_id, "reason": "unknown_decision"}
                    )
                    continue
                scope_path = decision.get("scopePath")
                if not scope_path:
                    scope_violations.append(
                        {"file": file_path, "decisionId": decision_id, "reason": "missing_scope_contract"}
                    )
                    continue
                scope_file = (repo_root / scope_path).resolve()
                if not scope_file.exists():
                    scope_violations.append(
                        {
                            "file": file_path,
                            "decisionId": decision_id,
                            "reason": "missing_scope_contract",
                            "scopePath": scope_path,
                        }
                    )
                    continue
                file_scopes.append(json.loads(scope_file.read_text()))

        if file_path not in changed_files:
            scope_violations.append({"file": file_path, "reason": "file_not_present_in_git_diff"})
            continue

        if not file_scopes:
            scope_violations.append({"file": file_path, "reason": "no_scope_contract"})
            continue

        if not _path_allowed(file_path, file_scopes):
            scope_violations.append({"file": file_path, "reason": "forbidden_path"})

        added_lines = _git_added_lines(repo_root, file_path)
        current_text = _read_working_tree_text(repo_root, file_path)
        scope_violations.extend(
            _scan_added_lines(file_path=file_path, added_lines=added_lines, scopes=file_scopes, current_text=current_text)
        )

        changed_symbols = _python_changed_symbols(repo_root, file_path) if _requires_symbol_accounting(file_path, file_scopes) else []
        if changed_symbols:
            python_symbol_changes.append({"file": file_path, "symbols": changed_symbols})
            accounted_symbols = {
                _symbol_key(symbol)
                for symbol in change.get("symbols", [])
                if _normalize_patch_symbol(symbol) is not None
            }
            for symbol in changed_symbols:
                key = _symbol_key(symbol)
                if key not in accounted_symbols:
                    scope_violations.append(
                        {
                            "file": file_path,
                            "reason": "unaccounted_symbol",
                            "symbol": symbol,
                        }
                    )

    ok = not authority_violations and not scope_violations
    certificate = {
        "ok": ok,
        "verifiedAt": _utc_now(),
        "runDir": str(run_path),
        "decisionIds": decision_ids,
        "baseGitSha": expected_git,
        "currentGitSha": current_git,
        "baseSourceSnapshot": expected_snapshot,
        "headSourceSnapshot": head_snapshot,
        "diffFiles": changed_files,
        "accountedFiles": sorted(accounted_files),
        "pythonSymbolChanges": python_symbol_changes,
        "authorityViolations": authority_violations,
        "scopeViolations": scope_violations,
        "patchLedgerPath": str(patch_path),
    }
    _write_json(run_path / "scope-certificate.json", certificate)

    if authority_violations:
        return {
            "ok": False,
            "error": {
                "code": "PATCH_AUTHORITY_DENIED",
                "message": "Patch ledger cites claims that are not implementation-authorized.",
                "details": {"violations": authority_violations},
            },
        }
    if scope_violations:
        return {
            "ok": False,
            "error": {
                "code": "PATCH_SCOPE_VIOLATION",
                "message": "Patch scope contract failed against the actual git diff.",
                "details": {"violations": scope_violations},
            },
        }
    return {
        "ok": True,
        "run_dir": str(run_path),
        "patch_ledger_path": str(patch_path),
        "scope_certificate_path": str(run_path / "scope-certificate.json"),
        "base_source_snapshot": expected_snapshot,
    }


def _build_source_ledger(*, task: str, sources: list[str], cwd: Path, max_files: int) -> dict:
    keywords = _keywords(task)
    workspace_root = _find_workspace_root(cwd)
    task_entry = {
        "sourceId": "SRC-TASK",
        "path": "task://prompt",
        "kind": "task",
        "sha256": _sha_text(task),
        "score": 10_000,
        "matchedKeywords": keywords,
        "snippets": [
            {
                "snippetId": "SNP-TASK-001",
                "lineStart": 1,
                "lineEnd": max(1, task.count("\n") + 1),
                "sha256": _sha_text(task),
                "text": task,
            }
        ],
    }

    candidates: list[dict] = []
    for raw_source in sources:
        source_path = (cwd / raw_source).resolve() if not os.path.isabs(raw_source) else Path(raw_source).resolve()
        for file_path in _iter_text_files(source_path):
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel_path = _relative_display_path(file_path, cwd, workspace_root)
            kind = _source_kind(rel_path)
            matched = [keyword for keyword in keywords if keyword in rel_path.lower() or keyword in text.lower()]
            score = _score_file(rel_path, text, matched, kind)
            candidates.append(
                {
                    "path": file_path,
                    "rel_path": rel_path,
                    "kind": kind,
                    "text": text,
                    "score": score,
                    "matched": matched,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["rel_path"]))
    selected: list[dict] = []
    for candidate in candidates:
        if len(selected) >= max_files:
            break
        if candidate["score"] <= 0 and selected:
            continue
        selected.append(candidate)
    if not selected:
        selected = candidates[:max_files]

    source_records: list[dict] = [task_entry]
    snapshot_entries: list[dict] = []
    for index, candidate in enumerate(selected, start=1):
        snippets = _extract_snippets(candidate["text"], candidate["matched"])
        record = {
            "sourceId": f"SRC-{index:04d}",
            "path": candidate["rel_path"],
            "kind": candidate["kind"],
            "sha256": _sha_text(candidate["text"]),
            "score": candidate["score"],
            "matchedKeywords": candidate["matched"],
            "snippets": snippets,
        }
        source_records.append(record)
        snapshot_entries.append({"path": candidate["rel_path"], "sha256": record["sha256"]})

    return {
        "generatedAt": _utc_now(),
        "baseGitSha": _git_sha(workspace_root),
        "baseSourceSnapshot": _sha_json(snapshot_entries),
        "selectedSources": source_records,
    }


def _build_claims(*, task: str, source_ledger: dict) -> list[dict]:
    claims: list[dict] = []
    claims.append(
        _claim(
            claim_id="CLM-TASK-001",
            text=f"Requested implementation scope: {task}",
            authority_class="implementation_fact",
            status="verified",
            source_refs=[{"sourceId": "SRC-TASK", "snippetId": "SNP-TASK-001"}],
            allowed_use=["planning", "implementation"],
            blocked_use=[],
        )
    )

    for source in source_ledger["selectedSources"]:
        if source["sourceId"] == "SRC-TASK":
            continue
        if source["kind"] == "decision":
            decision_id = _decision_id_from_path(source["path"])
            decision_text = _decision_summary_from_snippets(source["snippets"])
            claims.append(
                {
                    **_claim(
                        claim_id=f"CLM-{decision_id}",
                        text=decision_text,
                        authority_class="promoted_decision",
                        status="verified",
                        source_refs=[{"sourceId": source["sourceId"], "snippetId": source["snippets"][0]["snippetId"]}],
                        allowed_use=["planning", "implementation"],
                        blocked_use=[],
                    ),
                    "decisionId": decision_id,
                    "title": decision_text,
                    "path": source["path"],
                }
            )
            continue

        for snippet in source["snippets"][:2]:
            normalized = _normalize_claim_text(snippet["text"])
            if any(marker in normalized.lower() for marker in FORBIDDEN_PLANNING_MARKERS):
                claims.append(
                    _claim(
                        claim_id=f"CLM-{source['sourceId']}-{snippet['snippetId'].split('-')[-1]}-PLAN",
                        text=normalized,
                        authority_class="planning_inference",
                        status="partially_verified",
                        source_refs=[{"sourceId": source["sourceId"], "snippetId": snippet["snippetId"]}],
                        allowed_use=["planning"],
                        blocked_use=["implementation"],
                    )
                )
                continue
            claims.append(
                _claim(
                    claim_id=f"CLM-{source['sourceId']}-{snippet['snippetId'].split('-')[-1]}",
                    text=normalized,
                    authority_class="implementation_fact",
                    status="verified",
                    source_refs=[{"sourceId": source["sourceId"], "snippetId": snippet["snippetId"]}],
                    allowed_use=["planning", "implementation"],
                    blocked_use=[],
                )
            )

    claims.append(
        _claim(
            claim_id="CLM-EXEC-001",
            text=(
                f"The captured source snapshot {source_ledger['baseSourceSnapshot']} matches the ledger produced during this run."
            ),
            authority_class="execution_verified_fact",
            status="verified",
            source_refs=[],
            allowed_use=["planning", "implementation"],
            blocked_use=[],
        )
    )

    claims.append(
        _claim(
            claim_id="CLM-INF-001",
            text="Prefer implementing inside the existing CLI surface before adding any new front door.",
            authority_class="planning_inference",
            status="partially_verified",
            source_refs=[],
            allowed_use=["planning"],
            blocked_use=["implementation"],
        )
    )

    claims.append(
        _claim(
            claim_id="CLM-QUAR-001",
            text="NotebookLM remains quarantined until a callable, deterministic provider path is implemented and verified.",
            authority_class="quarantined_claim",
            status="source_missing",
            source_refs=[],
            allowed_use=["planning"],
            blocked_use=["implementation"],
        )
    )

    return _dedupe_claims(claims)


def _build_decisions(*, source_ledger: dict, claims: list[dict], repo_root: Path) -> list[dict]:
    decisions = []
    source_by_path = {source["path"]: source for source in source_ledger["selectedSources"]}
    for claim in claims:
        if claim["authorityClass"] != "promoted_decision":
            continue
        path = claim.get("path")
        scope_path = None
        if path:
            candidate = Path(path)
            if candidate.suffix == ".md":
                scope_candidate = candidate.with_suffix(".scope.json")
                if (repo_root / scope_candidate).exists():
                    scope_path = str(scope_candidate).replace("\\", "/")
        decisions.append(
            {
                "decisionId": claim["decisionId"],
                "title": claim.get("title", claim["text"]),
                "path": path,
                "scopePath": scope_path,
                "claimId": claim["claimId"],
            }
        )
    decisions.sort(key=lambda item: item["decisionId"])
    return decisions


def _build_context_pack(
    *,
    task: str,
    provider: str,
    run_id: str,
    provider_metadata: dict,
    source_ledger: dict,
    claims: list[dict],
    decisions: list[dict],
    workspace_root: Path,
) -> dict:
    return {
        "task": task,
        "provider": provider,
        "providerMetadata": provider_metadata,
        "runId": run_id,
        "workspaceRoot": str(workspace_root),
        "baseGitSha": source_ledger.get("baseGitSha"),
        "baseSourceSnapshot": source_ledger["baseSourceSnapshot"],
        "authorizedExecutorAuthorityClasses": sorted(ALLOWED_EXECUTOR_AUTHORITY),
        "claims": [
            {
                "claimId": claim["claimId"],
                "text": claim["text"],
                "authorityClass": claim["authorityClass"],
                "status": claim["status"],
                "allowedUse": claim["allowedUse"],
                "blockedUse": claim["blockedUse"],
                "sourceRefs": claim["sourceRefs"],
            }
            for claim in claims
        ],
        "decisions": decisions,
        "sources": [
            {
                "sourceId": source["sourceId"],
                "path": source["path"],
                "kind": source["kind"],
            }
            for source in source_ledger["selectedSources"]
        ],
        "artifacts": {
            "sourceLedger": "source-ledger.json",
            "claimLedger": "claim-ledger.json",
            "plannerContext": "planner-context.md",
            "executorContext": "executor-context.md",
            "providerOutput": "provider-output.md",
            "patchLedger": "patch-ledger.json",
            "scopeCertificate": "scope-certificate.json",
        },
    }


def _render_provider_output(
    *,
    task: str,
    provider: str,
    provider_metadata: dict,
    source_ledger: dict | None = None,
    claims: list[dict] | None = None,
) -> str:
    lines = [
        "# Provider Output",
        "",
        f"Task: {task}",
        f"Provider: {provider}",
        f"Status: {provider_metadata['status']}",
    ]
    mode = provider_metadata.get("mode")
    if mode:
        lines.append(f"Mode: {mode}")
    reason = provider_metadata.get("reason")
    if reason:
        lines.append(f"Reason: {reason}")
    smoke_command = provider_metadata.get("safeSmokeCommand")
    if smoke_command:
        lines.append(f"Safe smoke command: {smoke_command}")
    else:
        lines.append("Safe smoke command: none detected")

    lines.append("")
    lines.append("## Raw provider metadata")
    lines.append(json.dumps(provider_metadata, indent=2, sort_keys=True))

    adapter_result = provider_metadata.get("adapterResult")
    if adapter_result:
        lines.extend([
            "",
            "## Adapter skeleton result",
            f"- Contract: `{adapter_result.get('contractVersion')}`",
            f"- Status: {adapter_result.get('status')}",
            f"- OK: {adapter_result.get('ok')}",
            f"- Capture mode: `{adapter_result.get('capture', {}).get('mode')}`",
            "- Authority:",
            f"  - May create claims: {adapter_result.get('authority', {}).get('mayCreateClaims')}",
            f"  - May authorize implementation: {adapter_result.get('authority', {}).get('mayAuthorizeImplementation')}",
            f"  - Requires local promotion: {adapter_result.get('authority', {}).get('requiresLocalPromotion')}",
        ])
        adapter_errors = adapter_result.get("errors", [])
        if adapter_errors:
            lines.append("- Adapter/preflight errors:")
            for error in adapter_errors:
                lines.append(f"  - `{error.get('code')}` {error.get('message')}")

    promotion_decision = provider_metadata.get("promotionDecision")
    if promotion_decision:
        lines.extend([
            "",
            "## Promotion policy decision",
            f"- Target: `{promotion_decision.get('target')}`",
            f"- OK: {promotion_decision.get('ok')}",
            f"- Can enter executor context: {promotion_decision.get('canEnterExecutorContext')}",
            f"- Can authorize patch: {promotion_decision.get('canAuthorizePatch')}",
            f"- Requires local promotion: {promotion_decision.get('requiresLocalPromotion')}",
        ])
        promotion_errors = promotion_decision.get("errors", [])
        if promotion_errors:
            lines.append("- Promotion errors:")
            for error in promotion_errors:
                lines.append(f"  - `{error.get('code')}` {error.get('message')}")

    if source_ledger is not None:
        lines.extend([
            "",
            f"Base source snapshot: {source_ledger['baseSourceSnapshot']}",
            "",
            "## Selected sources",
        ])
        for source in source_ledger["selectedSources"]:
            lines.append(f"- `{source['sourceId']}` {source['path']} ({source['kind']})")
            for snippet in source["snippets"]:
                lines.append(f"  - `{snippet['snippetId']}` lines {snippet['lineStart']}-{snippet['lineEnd']}: {snippet['text']}")

    if claims is not None:
        lines.append("")
        lines.append("## Claims")
        for claim in claims:
            lines.append(
                f"- `{claim['claimId']}` [{claim['authorityClass']}/{claim['status']}] {claim['text']}"
            )
    errors = provider_metadata.get("errors", [])
    if errors:
        lines.append("")
        lines.append("## Preflight errors")
        for error in errors:
            lines.append(f"- `{error['code']}` {error['message']}")
    lines.append("")
    return "\n".join(lines)


def _render_planner_context(*, task: str, context_pack: dict, claims: list[dict]) -> str:
    lines = [
        "# planner-context.md",
        "",
        f"Task: {task}",
        f"Base source snapshot: `{context_pack['baseSourceSnapshot']}`",
        "",
        "## implementation_authority",
    ]
    for claim in claims:
        if claim["authorityClass"] in ALLOWED_EXECUTOR_AUTHORITY and claim["status"] == "verified":
            lines.append(f"- `{claim['claimId']}` {claim['text']}")
    lines.append("")
    lines.append("## promoted_decisions")
    for claim in claims:
        if claim["authorityClass"] == "promoted_decision":
            lines.append(f"- `{claim['claimId']}` {claim['text']}")
    lines.append("")
    lines.append("## design_inference")
    for claim in claims:
        if claim["authorityClass"] == "planning_inference":
            lines.append(f"- `{claim['claimId']}` {claim['text']}")
    lines.append("")
    lines.append("## quarantined_claims")
    for claim in claims:
        if claim["authorityClass"] == "quarantined_claim":
            lines.append(f"- `{claim['claimId']}` {claim['text']}")
    lines.append("")
    return "\n".join(lines)


def _render_executor_context(*, task: str, context_pack: dict, claims: list[dict]) -> str:
    lines = [
        "# executor-context.md",
        "",
        f"Task: {task}",
        f"Base source snapshot: `{context_pack['baseSourceSnapshot']}`",
        "",
        "## implementation_authorized_claims",
    ]
    for claim in claims:
        if claim["authorityClass"] not in ALLOWED_EXECUTOR_AUTHORITY:
            continue
        if claim["status"] != "verified":
            continue
        if any(marker in claim["text"].lower() for marker in FORBIDDEN_PLANNING_MARKERS):
            continue
        lines.append(f"- `{claim['claimId']}` [{claim['authorityClass']}] {claim['text']}")
    lines.append("")
    lines.append("## promoted_decisions")
    for claim in claims:
        if claim["authorityClass"] == "promoted_decision" and claim["status"] == "verified":
            lines.append(f"- `{claim['claimId']}` {claim['text']}")
    lines.append("")
    lines.append("Planning-only material omitted by authority filter.")
    lines.append("")
    return "\n".join(lines)


def _write_failed_manifest(
    *,
    run_dir: Path,
    task: str,
    provider: str,
    provider_metadata: dict,
    provider_output_path: Path,
    out_path: str,
    workspace_root: Path,
    working_dir: Path,
    started: float,
    error: DossierError,
) -> dict:
    provider_output_path.write_text(
        _render_provider_output(
            task=task,
            provider=provider,
            provider_metadata=provider_metadata,
        )
    )
    manifest = {
        "runId": run_dir.name,
        "task": task,
        "provider": provider,
        "providerMetadata": provider_metadata,
        "providerMeta": provider_metadata,
        "workspaceRoot": str(workspace_root),
        "workingDirectory": str(working_dir),
        "requestedOutPath": out_path,
        "providerOutputPath": str(provider_output_path),
        "startedAt": _utc_now(),
        "durationMs": int((time.time() - started) * 1000),
        "ok": False,
        "error": error.to_error(),
        "notebooklm": _legacy_notebooklm_status(provider_metadata),
    }
    _write_json(run_dir / "manifest.json", manifest)
    return {
        "ok": False,
        "provider": provider,
        "provider_meta": provider_metadata,
        "run_dir": str(run_dir),
        "error": error.to_error(),
        "manifest_path": str(run_dir / "manifest.json"),
        "provider_output_path": str(provider_output_path),
    }


def _find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "package.json").exists():
            return candidate
    return current


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"dossier-{stamp}-{uuid.uuid4().hex[:8]}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_provider_metadata(provider: str) -> dict:
    if provider == "local":
        return {
            "provider": "local",
            "status": "available",
            "mode": "deterministic_local",
            "reason": "Local dossier backend is bundled with dossier-core.",
            "safeSmokeCommand": None,
            "moduleChecks": [],
            "matchingDistributions": [],
            "cliCandidates": [],
        }
    if provider == "notebooklm":
        return _detect_notebooklm_environment()
    return {
        "provider": provider,
        "status": "unsupported",
        "mode": "unknown",
        "reason": f"Unsupported dossier provider '{provider}'.",
        "safeSmokeCommand": None,
        "moduleChecks": [],
        "matchingDistributions": [],
        "cliCandidates": [],
    }


def _provider_error(provider_metadata: dict) -> DossierError | None:
    provider = provider_metadata["provider"]
    if provider == "local" and provider_metadata["status"] == "available":
        return None
    if provider == "notebooklm":
        status = provider_metadata.get("status")
        if status == "not_ready":
            return DossierError(
                "PROVIDER_NOT_READY",
                "NotebookLM provider preflight detected tooling, but the adapter is not ready.",
                details=provider_metadata,
            )
        return DossierError(
            "PROVIDER_UNAVAILABLE",
            "NotebookLM provider is recognized but unavailable in this environment.",
            details=provider_metadata,
        )
    return DossierError(
        "UNSUPPORTED_PROVIDER",
        f"Unsupported dossier provider '{provider}'.",
        details=provider_metadata,
    )


def _detect_notebooklm_environment() -> dict:
    return preflight_notebooklm_provider()


def _detect_notebooklm_provider() -> dict:
    return _detect_notebooklm_environment()


def _legacy_notebooklm_status(provider_metadata: dict) -> dict:
    if provider_metadata["provider"] != "notebooklm":
        return {"status": "not_requested"}
    return {
        "status": provider_metadata["status"],
        "safeSmokeCommand": provider_metadata.get("safeSmokeCommand"),
    }


def _keywords(task: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_]+", task.lower())
    uniq: list[str] = []
    for token in tokens:
        if len(token) < 3 or token in STOPWORDS:
            continue
        if token not in uniq:
            uniq.append(token)
    return uniq[:12]


def _iter_text_files(path: Path) -> Iterable[Path]:
    if not path.exists():
        return []
    if path.is_file():
        if path.name.endswith(".scope.json"):
            return []
        return [path] if path.suffix.lower() in TEXT_EXTENSIONS else []

    files: list[Path] = []
    for root, dirnames, filenames in os.walk(path):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in SKIP_DIRS]
        for filename in sorted(filenames):
            file_path = Path(root) / filename
            if file_path.name.endswith(".scope.json"):
                continue
            if file_path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if file_path.stat().st_size > 200_000:
                continue
            files.append(file_path)
    return files


def _relative_display_path(path: Path, cwd: Path, workspace_root: Path) -> str:
    for base in (workspace_root, cwd):
        try:
            return str(path.relative_to(base)).replace('\\', '/')
        except ValueError:
            continue
    return str(path).replace('\\', '/')


def _source_kind(display_path: str) -> str:
    if display_path.startswith("docs/decisions/") and display_path.endswith(".md"):
        return "decision"
    if display_path.startswith("docs/research/"):
        return "research"
    if display_path.endswith("AGENTS.md") or display_path.startswith("tasks/") or display_path.startswith(".omx/"):
        return "policy"
    if Path(display_path).suffix.lower() in {".py", ".ts", ".tsx", ".js", ".cjs", ".mjs"}:
        return "code"
    return "reference"


def _score_file(display_path: str, text: str, matched: list[str], kind: str) -> int:
    score = len(matched) * 10
    lower_path = display_path.lower()
    lower_text = text.lower()
    for keyword in matched:
        score += lower_path.count(keyword) * 3
        score += min(5, lower_text.count(keyword))
    if kind == "decision":
        score += 50
    if lower_path.endswith("cli.py"):
        score += 15
    if lower_path.endswith("task.md"):
        score += 10
    return score


def _extract_snippets(text: str, keywords: list[str], max_snippets: int = 2) -> list[dict]:
    lines = text.splitlines()
    if not lines:
        lines = [text]
    indexes: list[int] = []
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            indexes.append(idx)
    if not indexes:
        indexes = [0]

    snippets: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for count, idx in enumerate(indexes[:max_snippets], start=1):
        start = max(0, idx - 1)
        end = min(len(lines), idx + 2)
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        snippet_text = " ".join(line.strip() for line in lines[start:end] if line.strip())
        snippets.append(
            {
                "snippetId": f"SNP-{count:03d}",
                "lineStart": start + 1,
                "lineEnd": end,
                "sha256": _sha_text(snippet_text),
                "text": snippet_text,
            }
        )
    return snippets


def _normalize_claim_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:280]


def _decision_id_from_path(path: str) -> str:
    stem = Path(path).stem
    match = re.match(r"(DEC-\d+)", stem)
    return match.group(1) if match else stem


def _decision_summary_from_snippets(snippets: list[dict]) -> str:
    for snippet in snippets:
        text = _normalize_claim_text(snippet["text"])
        if text and not text.startswith("#"):
            return text
    return _normalize_claim_text(snippets[0]["text"])


def _claim(
    *,
    claim_id: str,
    text: str,
    authority_class: str,
    status: str,
    source_refs: list[dict],
    allowed_use: list[str],
    blocked_use: list[str],
) -> dict:
    return {
        "claimId": claim_id,
        "text": text,
        "authorityClass": authority_class,
        "status": status,
        "sourceRefs": source_refs,
        "allowedUse": allowed_use,
        "blockedUse": blocked_use,
    }


def _dedupe_claims(claims: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        key = (claim["claimId"], claim["authorityClass"], claim["text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def _sha_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _sha_json(data: list[dict]) -> str:
    return _sha_text(json.dumps(data, sort_keys=True))


def _git_sha(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None



def _ignored_diff_paths(*, repo_root: Path, run_path: Path, manifest: dict) -> set[str]:
    ignored: set[str] = set()
    if run_path.exists():
        for file_path in run_path.rglob('*'):
            if file_path.is_file():
                try:
                    ignored.add(str(file_path.relative_to(repo_root)).replace('\\', '/'))
                except ValueError:
                    pass
    requested = manifest.get("requestedOutPath")
    if requested:
        requested_path = Path(requested)
        if requested_path.exists():
            try:
                ignored.add(str(requested_path.relative_to(repo_root)).replace('\\', '/'))
            except ValueError:
                pass
    return ignored

def _git_changed_files(repo_root: Path) -> list[str]:
    files: set[str] = set()
    try:
        diff = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD", "--"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        files.update(path.strip() for path in diff if path.strip())
    except Exception:
        pass
    try:
        untracked = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        files.update(path.strip() for path in untracked if path.strip())
    except Exception:
        pass
    return sorted(files)


def _git_added_lines(repo_root: Path, file_path: str) -> list[str]:
    absolute = repo_root / file_path
    added_lines: list[str] = []
    if absolute.exists():
        try:
            diff = subprocess.run(
                ["git", "-C", str(repo_root), "diff", "--no-color", "--unified=0", "HEAD", "--", file_path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            for line in diff:
                if line.startswith("+++") or not line.startswith("+"):
                    continue
                added_lines.append(line[1:])
        except Exception:
            pass
    if not added_lines and absolute.exists():
        added_lines = absolute.read_text(encoding="utf-8", errors="ignore").splitlines()
    return added_lines


def _read_working_tree_text(repo_root: Path, file_path: str) -> str | None:
    absolute = repo_root / file_path
    if not absolute.exists():
        return None
    return absolute.read_text(encoding="utf-8", errors="ignore")


def _git_show_text(repo_root: Path, file_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"HEAD:{file_path}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout


def _compute_head_snapshot(source_ledger: dict, repo_root: Path) -> str:
    snapshot_entries: list[dict] = []
    git_available = _git_sha(repo_root) is not None
    for source in source_ledger.get("selectedSources", []):
        path = source["path"]
        if path.startswith("task://"):
            continue
        digest = None
        if git_available:
            try:
                result = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f"HEAD:{path}"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                digest = _sha_text(result.stdout)
            except Exception:
                digest = None
        else:
            file_path = repo_root / path
            if file_path.exists():
                digest = _sha_text(file_path.read_text(encoding="utf-8", errors="ignore"))
        snapshot_entries.append({"path": path, "sha256": digest})
    return _sha_json(snapshot_entries)


def _path_allowed(file_path: str, scopes: list[dict]) -> bool:
    allowed_patterns = [pattern for scope in scopes for pattern in scope.get("allowedPaths", [])]
    forbidden_patterns = [pattern for scope in scopes for pattern in scope.get("forbiddenPaths", [])]
    if any(fnmatch(file_path, pattern) for pattern in forbidden_patterns):
        return False
    return any(fnmatch(file_path, pattern) for pattern in allowed_patterns)


def _requires_symbol_accounting(file_path: str, scopes: list[dict]) -> bool:
    if not file_path.endswith(".py"):
        return False
    for scope in scopes:
        rule = scope.get("symbolAccounting", {})
        if not isinstance(rule, dict):
            continue
        if rule.get("required") and rule.get("language", "python") == "python":
            return True
    return False


def _scan_added_lines(*, file_path: str, added_lines: list[str], scopes: list[dict], current_text: str | None) -> list[dict]:
    violations: list[dict] = []
    forbidden_strings = [value for scope in scopes for value in scope.get("forbiddenStrings", [])]
    forbidden_imports = [value for scope in scopes for value in scope.get("forbiddenImports", [])]
    forbidden_capabilities = [value for scope in scopes for value in scope.get("forbiddenCapabilities", [])]
    joined = "\n".join(added_lines)
    for token in forbidden_strings:
        if token and token in joined:
            violations.append({"file": file_path, "reason": "forbidden_string", "token": token})
    for token in forbidden_imports:
        if not token:
            continue
        patterns = [
            re.compile(rf"\bimport\s+{re.escape(token)}\b"),
            re.compile(rf"\bfrom\s+{re.escape(token)}\b"),
        ]
        if any(pattern.search(joined) for pattern in patterns):
            violations.append({"file": file_path, "reason": "forbidden_import", "token": token})
    if current_text and file_path.endswith(".py"):
        ast_details = _python_ast_details(current_text)
        for rule in forbidden_capabilities:
            capability = rule.get("name", "unknown_capability")
            for token in rule.get("pythonImports", []):
                if token and token in ast_details["imports"]:
                    violations.append(
                        {
                            "file": file_path,
                            "reason": "forbidden_capability",
                            "capability": capability,
                            "token": token,
                        }
                    )
            for token in rule.get("pythonCalls", []):
                if token and token in ast_details["calls"]:
                    violations.append(
                        {
                            "file": file_path,
                            "reason": "forbidden_capability",
                            "capability": capability,
                            "token": token,
                        }
                    )
            for token in rule.get("stringPatterns", []):
                if token and token in joined:
                    violations.append(
                        {
                            "file": file_path,
                            "reason": "forbidden_capability",
                            "capability": capability,
                            "token": token,
                        }
                    )
    return violations


def _python_changed_symbols(repo_root: Path, file_path: str) -> list[dict]:
    if not file_path.endswith(".py"):
        return []
    current_text = _read_working_tree_text(repo_root, file_path)
    if current_text is None:
        return []
    before_details = _python_ast_details(_git_show_text(repo_root, file_path))
    after_details = _python_ast_details(current_text)
    before_index = {(_symbol_key(symbol)): symbol for symbol in before_details["symbols"]}
    changed: list[dict] = []
    for symbol in after_details["symbols"]:
        key = _symbol_key(symbol)
        previous = before_index.get(key)
        if previous is None:
            changed.append({k: v for k, v in symbol.items() if k != "digest"} | {"change": "added"})
            continue
        if previous["digest"] != symbol["digest"]:
            changed.append({k: v for k, v in symbol.items() if k != "digest"} | {"change": "modified"})
    changed.sort(key=lambda item: (item["kind"], item["name"]))
    return changed


def _python_ast_details(source_text: str | None) -> dict:
    if not source_text:
        return {"symbols": [], "imports": set(), "calls": set()}
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return {"symbols": [], "imports": set(), "calls": set()}

    symbols: list[dict] = []
    imports: set[str] = set()
    calls: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbol = {
                    "kind": "import",
                    "name": alias.name,
                    "digest": alias.name,
                }
                symbols.append(symbol)
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imported = f"{module}.{alias.name}" if module else alias.name
                symbol = {
                    "kind": "import",
                    "name": imported,
                    "digest": imported,
                }
                symbols.append(symbol)
                imports.add(imported)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            digest = _sha_text(ast.get_source_segment(source_text, node) or ast.unparse(node))
            symbols.append({"kind": "function", "name": node.name, "digest": digest})
        elif isinstance(node, ast.ClassDef):
            digest = _sha_text(ast.get_source_segment(source_text, node) or ast.unparse(node))
            symbols.append({"kind": "class", "name": node.name, "digest": digest})

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _call_name(node.func)
        if call_name:
            calls.add(call_name)

    return {"symbols": symbols, "imports": imports, "calls": calls}


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _normalize_patch_symbol(symbol: dict | str) -> dict | None:
    if isinstance(symbol, str):
        if ":" not in symbol:
            return None
        kind, name = symbol.split(":", 1)
        if kind and name:
            return {"kind": kind, "name": name}
        return None
    if isinstance(symbol, dict):
        kind = symbol.get("kind")
        name = symbol.get("name")
        if kind and name:
            return {"kind": str(kind), "name": str(name)}
    return None


def _symbol_key(symbol: dict | str) -> str:
    normalized = _normalize_patch_symbol(symbol)
    if not normalized:
        return ""
    return f"{normalized['kind']}:{normalized['name']}"
