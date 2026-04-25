from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from polyglot.dossier import generate_dossier


class NotebookLMPromotionWireTests(unittest.TestCase):
    def test_notebooklm_dossier_records_promotion_decision_and_blocks_executor_context(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            source.write_text("# Source\n\nNotebookLM promotion wire evidence.\n")
            out = root / "out" / "executor-context.md"

            preflight = {
                "provider": "notebooklm",
                "status": "not_ready",
                "mode": "provider_preflight",
                "reason": "Tooling detected but live adapter is not verified.",
                "safeSmokeCommand": "notebooklm --help",
                "preflight": {
                    "storage": {
                        "source": "NOTEBOOKLM_HOME",
                        "path": str(root / ".notebooklm" / "storage_state.json"),
                        "exists": False,
                    }
                },
                "moduleChecks": [],
                "matchingDistributions": [],
                "cliCandidates": [],
                "errors": [
                    {
                        "code": "NOTEBOOKLM_READY_UNVERIFIED",
                        "message": "Live capture is not verified.",
                        "details": {},
                    }
                ],
            }

            old_cwd = Path.cwd()
            try:
                os.chdir(root)
                with mock.patch("polyglot.dossier._detect_notebooklm_environment", return_value=preflight):
                    result = generate_dossier(
                        task="Use NotebookLM provider skeleton metadata.",
                        provider="notebooklm",
                        sources=[str(source)],
                        out_path=str(out),
                    )
            finally:
                os.chdir(old_cwd)

            self.assertFalse(result["ok"], result)
            run_dir = Path(result["run_dir"])
            manifest = json.loads((run_dir / "manifest.json").read_text())
            provider_meta = manifest["providerMeta"]
            decision = provider_meta["promotionDecision"]

            self.assertEqual(decision["schemaVersion"], "notebooklm-promotion-decision-v0")
            self.assertEqual(decision["provider"], "notebooklm")
            self.assertEqual(decision["target"], "executor_context")
            self.assertFalse(decision["ok"])
            self.assertFalse(decision["canEnterExecutorContext"])
            self.assertFalse(decision["canAuthorizePatch"])
            self.assertTrue(provider_meta["plannerOnlyUntilLocalPromotion"])
            self.assertEqual(decision["errors"][0]["code"], "NOTEBOOKLM_PROVIDER_RESULT_NOT_CAPTURED")

            provider_output = (run_dir / "provider-output.md").read_text()
            self.assertIn("## Promotion policy decision", provider_output)
            self.assertIn("Can enter executor context: False", provider_output)
            self.assertIn("Can authorize patch: False", provider_output)
            self.assertIn("NOTEBOOKLM_PROVIDER_RESULT_NOT_CAPTURED", provider_output)


if __name__ == "__main__":
    unittest.main()
