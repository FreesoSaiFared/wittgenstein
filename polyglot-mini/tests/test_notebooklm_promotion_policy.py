from __future__ import annotations

import json
import unittest
from pathlib import Path

from polyglot.notebooklm_promotion_policy import (
    PROMOTION_SCHEMA_VERSION,
    evaluate_notebooklm_provider_promotion,
)


class NotebookLMPromotionPolicyTests(unittest.TestCase):
    def provider_result_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "artifacts"
            / "manual-gated"
            / "notebooklm"
            / "provider-result-conversion-fixture"
            / "provider-result.json"
        )

    def provider_result(self) -> dict:
        return json.loads(self.provider_result_path().read_text())

    def valid_promotion(self) -> dict:
        return {
            "schemaVersion": PROMOTION_SCHEMA_VERSION,
            "provider": "notebooklm",
            "sourceProviderResultContractVersion": "notebooklm-provider-result-v0",
            "allowedTargets": ["executor_context"],
            "allowsPatchAuthority": False,
            "localVerification": {
                "status": "verified",
                "method": "synthetic fixture shape only",
            },
        }

    def test_captured_provider_result_is_blocked_without_local_promotion(self) -> None:
        decision = evaluate_notebooklm_provider_promotion(self.provider_result(), target="executor_context")

        self.assertFalse(decision["ok"])
        self.assertFalse(decision["canEnterExecutorContext"])
        self.assertFalse(decision["canAuthorizePatch"])
        self.assertEqual(decision["errors"][0]["code"], "NOTEBOOKLM_LOCAL_PROMOTION_REQUIRED")
        self.assertTrue(decision["requiresLocalPromotion"])

    def test_captured_provider_result_cannot_authorize_patch_without_promotion(self) -> None:
        decision = evaluate_notebooklm_provider_promotion(self.provider_result(), target="patch_authority")

        self.assertFalse(decision["ok"])
        self.assertFalse(decision["canEnterExecutorContext"])
        self.assertFalse(decision["canAuthorizePatch"])
        self.assertEqual(decision["errors"][0]["code"], "NOTEBOOKLM_LOCAL_PROMOTION_REQUIRED")

    def test_local_promotion_can_allow_executor_context_but_not_patch_authority(self) -> None:
        promotion = self.valid_promotion()

        executor_decision = evaluate_notebooklm_provider_promotion(
            self.provider_result(),
            promotion_artifact=promotion,
            target="executor_context",
        )
        patch_decision = evaluate_notebooklm_provider_promotion(
            self.provider_result(),
            promotion_artifact=promotion,
            target="patch_authority",
        )

        self.assertTrue(executor_decision["ok"])
        self.assertTrue(executor_decision["canEnterExecutorContext"])
        self.assertFalse(executor_decision["canAuthorizePatch"])

        self.assertFalse(patch_decision["ok"])
        self.assertFalse(patch_decision["canAuthorizePatch"])
        self.assertEqual(patch_decision["errors"][0]["code"], "NOTEBOOKLM_LOCAL_PROMOTION_TARGET_NOT_ALLOWED")

    def test_unverified_local_promotion_fails_closed(self) -> None:
        promotion = self.valid_promotion()
        promotion["localVerification"] = {"status": "claimed"}

        decision = evaluate_notebooklm_provider_promotion(
            self.provider_result(),
            promotion_artifact=promotion,
            target="executor_context",
        )

        self.assertFalse(decision["ok"])
        self.assertFalse(decision["canEnterExecutorContext"])
        self.assertEqual(decision["errors"][0]["code"], "NOTEBOOKLM_LOCAL_VERIFICATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
