from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from polyglot.notebooklm_adapter import (
    ADAPTER_ERROR_NOT_WIRED,
    CONTRACT_VERSION,
    build_notebooklm_provider_request,
    run_notebooklm_provider_adapter,
)


class NotebookLMAdapterSkeletonTests(unittest.TestCase):
    def test_request_is_metadata_only_and_authority_constrained(self) -> None:
        request = build_notebooklm_provider_request(
            task="Summarize the dossier boundary.",
            run_id="dossier-test-run",
            workspace_root=Path("/repo"),
            working_directory=Path("/repo/sub"),
            base_git_sha="abc123",
            base_source_snapshot="snapshot123",
            source_ledger_path="artifacts/runs/x/source-ledger.json",
            claim_ledger_path="artifacts/runs/x/claim-ledger.json",
            requested_out_path="/tmp/out.md",
        )

        self.assertEqual(request["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(request["provider"], "notebooklm")
        self.assertEqual(request["runId"], "dossier-test-run")
        self.assertTrue(request["constraints"]["noImplementationAuthority"])
        self.assertTrue(request["constraints"]["offlineReplayRequired"])
        self.assertFalse(request["constraints"]["allowNotebookMutation"])
        self.assertFalse(request["constraints"]["allowSourceUpload"])
        self.assertNotIn("sourceText", request)
        self.assertNotIn("sources", request)

    def test_skeleton_returns_structured_not_ready_result(self) -> None:
        request = build_notebooklm_provider_request(
            task="Use NotebookLM as provider evidence.",
            run_id="dossier-test-run",
            workspace_root="/repo",
            working_directory="/repo",
        )
        preflight = {
            "provider": "notebooklm",
            "status": "not_ready",
            "errors": [
                {
                    "code": "NOTEBOOKLM_READY_UNVERIFIED",
                    "message": "Not verified.",
                    "details": {},
                }
            ],
        }

        result = run_notebooklm_provider_adapter(request=request, preflight=preflight)

        self.assertFalse(result["ok"])
        self.assertEqual(result["provider"], "notebooklm")
        self.assertEqual(result["status"], "not_ready")
        self.assertEqual(result["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(result["capture"]["mode"], "none")
        self.assertFalse(result["authority"]["mayCreateClaims"])
        self.assertFalse(result["authority"]["mayAuthorizeImplementation"])
        self.assertTrue(result["authority"]["requiresLocalPromotion"])
        codes = {error["code"] for error in result["errors"]}
        self.assertIn("NOTEBOOKLM_READY_UNVERIFIED", codes)
        self.assertIn(ADAPTER_ERROR_NOT_WIRED, codes)

    def test_skeleton_does_not_run_subprocess_or_network_calls(self) -> None:
        request = build_notebooklm_provider_request(
            task="No live calls.",
            run_id="dossier-test-run",
            workspace_root="/repo",
            working_directory="/repo",
        )
        with mock.patch("polyglot.notebooklm_adapter.preflight_notebooklm_provider") as preflight_mock:
            preflight_mock.return_value = {"provider": "notebooklm", "status": "not_ready", "errors": []}
            result = run_notebooklm_provider_adapter(request=request)

        self.assertFalse(result["ok"])
        preflight_mock.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
