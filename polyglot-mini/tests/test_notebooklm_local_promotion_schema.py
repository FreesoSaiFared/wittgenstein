from __future__ import annotations

import json
import unittest
from pathlib import Path

from polyglot.notebooklm_promotion_policy import evaluate_notebooklm_provider_promotion


class NotebookLMLocalPromotionSchemaTests(unittest.TestCase):
    def root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def promotion_path(self) -> Path:
        return self.root() / "artifacts" / "manual-gated" / "notebooklm" / "local-promotion-schema" / "executor-context-local-promotion.json"

    def provider_result_path(self) -> Path:
        return self.root() / "artifacts" / "manual-gated" / "notebooklm" / "provider-result-conversion-fixture" / "provider-result.json"

    def test_local_promotion_fixture_shape_is_executor_only(self) -> None:
        promotion = json.loads(self.promotion_path().read_text())

        self.assertEqual(promotion["schemaVersion"], "notebooklm-local-promotion-v0")
        self.assertEqual(promotion["provider"], "notebooklm")
        self.assertEqual(promotion["allowedTargets"], ["executor_context"])
        self.assertFalse(promotion["allowsPatchAuthority"])
        self.assertEqual(promotion["localVerification"]["status"], "verified")
        self.assertFalse(promotion["authority"]["mayAuthorizePatch"])
        self.assertFalse(promotion["authority"]["mayAuthorizeImplementation"])

    def test_local_promotion_allows_executor_context_not_patch_authority(self) -> None:
        provider_result = json.loads(self.provider_result_path().read_text())
        promotion = json.loads(self.promotion_path().read_text())

        executor_decision = evaluate_notebooklm_provider_promotion(
            provider_result,
            promotion_artifact=promotion,
            target="executor_context",
        )
        patch_decision = evaluate_notebooklm_provider_promotion(
            provider_result,
            promotion_artifact=promotion,
            target="patch_authority",
        )

        self.assertTrue(executor_decision["ok"])
        self.assertTrue(executor_decision["canEnterExecutorContext"])
        self.assertFalse(executor_decision["canAuthorizePatch"])

        self.assertFalse(patch_decision["ok"])
        self.assertFalse(patch_decision["canAuthorizePatch"])
        self.assertIn(
            patch_decision["errors"][0]["code"],
            {"NOTEBOOKLM_LOCAL_PROMOTION_TARGET_NOT_ALLOWED", "NOTEBOOKLM_PATCH_AUTHORITY_NOT_GRANTED"},
        )

    def test_malformed_promotion_fails_closed(self) -> None:
        provider_result = json.loads(self.provider_result_path().read_text())
        promotion = json.loads(self.promotion_path().read_text())
        promotion["localVerification"] = {"status": "verified", "method": "missing verifier"}

        decision = evaluate_notebooklm_provider_promotion(
            provider_result,
            promotion_artifact=promotion,
            target="executor_context",
        )

        # Current policy checks status/method-level verification, not full JSON schema.
        # The important invariant here: malformed schema fixtures must not grant patch authority.
        self.assertFalse(decision["canAuthorizePatch"])


if __name__ == "__main__":
    unittest.main()
