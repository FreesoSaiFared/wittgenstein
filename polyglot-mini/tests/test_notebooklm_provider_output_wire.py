from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from polyglot.dossier import generate_dossier


class NotebookLMProviderOutputWireTests(unittest.TestCase):
    def test_notebooklm_provider_metadata_includes_adapter_skeleton_result(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            source.write_text("# Source\n\nNotebookLM provider seam evidence.\n")
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
            self.assertEqual(result["error"]["code"], "PROVIDER_NOT_READY")

            run_dir = Path(result["run_dir"])
            manifest = json.loads((run_dir / "manifest.json").read_text())
            provider_meta = manifest["providerMeta"]
            self.assertEqual(provider_meta["contractVersion"], "notebooklm-provider-result-v0")
            self.assertEqual(provider_meta["adapterStatus"], "not_ready")
            self.assertIn("adapterResult", provider_meta)

            adapter_result = provider_meta["adapterResult"]
            self.assertFalse(adapter_result["ok"])
            self.assertEqual(adapter_result["status"], "not_ready")
            self.assertEqual(adapter_result["capture"]["mode"], "none")
            self.assertFalse(adapter_result["authority"]["mayAuthorizeImplementation"])
            self.assertTrue(adapter_result["authority"]["requiresLocalPromotion"])

            codes = {error["code"] for error in adapter_result["errors"]}
            self.assertIn("NOTEBOOKLM_READY_UNVERIFIED", codes)
            self.assertIn("NOTEBOOKLM_ADAPTER_NOT_WIRED", codes)

            provider_output = (run_dir / "provider-output.md").read_text()
            self.assertIn("## Adapter skeleton result", provider_output)
            self.assertIn("Contract: `notebooklm-provider-result-v0`", provider_output)
            self.assertIn("May authorize implementation: False", provider_output)
            self.assertIn("NOTEBOOKLM_ADAPTER_NOT_WIRED", provider_output)


if __name__ == "__main__":
    unittest.main()
