from __future__ import annotations

import json
import unittest
from pathlib import Path

from polyglot.notebooklm_promotion_policy import (
    evaluate_notebooklm_provider_promotion,
    validate_local_promotion_artifact,
)


class NotebookLMPromotionValidationTests(unittest.TestCase):
    def root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def promotion_fixture(self) -> dict:
        path = self.root() / "artifacts" / "manual-gated" / "notebooklm" / "local-promotion-schema" / "executor-context-local-promotion.json"
        return json.loads(path.read_text())

    def provider_result(self) -> dict:
        path = self.root() / "artifacts" / "manual-gated" / "notebooklm" / "provider-result-conversion-fixture" / "provider-result.json"
        return json.loads(path.read_text())

    def test_valid_local_promotion_passes_code_level_validation(self) -> None:
        validation = validate_local_promotion_artifact(self.promotion_fixture())

        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["schemaVersion"], "notebooklm-local-promotion-validation-v0")
        self.assertEqual(validation["allowedTargets"], ["executor_context"])
        self.assertFalse(validation["allowsPatchAuthority"])
        self.assertEqual(validation["errors"], [])

    def test_missing_verified_by_fails_closed(self) -> None:
        promotion = self.promotion_fixture()
        promotion["localVerification"].pop("verifiedBy")

        validation = validate_local_promotion_artifact(promotion)
        decision = evaluate_notebooklm_provider_promotion(
            self.provider_result(),
            promotion_artifact=promotion,
            target="executor_context",
        )

        self.assertFalse(validation["ok"])
        self.assertEqual(validation["errors"][0]["code"], "NOTEBOOKLM_LOCAL_VERIFICATION_ACTOR_REQUIRED")
        self.assertFalse(decision["ok"])
        self.assertFalse(decision["canEnterExecutorContext"])
        self.assertFalse(decision["canAuthorizePatch"])
        self.assertEqual(decision["errors"][0]["code"], "NOTEBOOKLM_LOCAL_PROMOTION_SCHEMA_INVALID")

    def test_patch_authority_smuggling_fails_validation(self) -> None:
        promotion = self.promotion_fixture()
        promotion["allowedTargets"] = ["executor_context", "patch_authority"]
        promotion["allowsPatchAuthority"] = True
        promotion["authority"]["mayAuthorizePatch"] = True

        validation = validate_local_promotion_artifact(promotion)
        codes = {error["code"] for error in validation["errors"]}

        self.assertFalse(validation["ok"])
        self.assertIn("NOTEBOOKLM_LOCAL_PROMOTION_TARGET_INVALID", codes)
        self.assertIn("NOTEBOOKLM_LOCAL_PROMOTION_PATCH_AUTHORITY_FORBIDDEN", codes)
        self.assertIn("NOTEBOOKLM_LOCAL_PROMOTION_AUTHORITY_INVALID", codes)

    def test_authority_boundary_must_be_exact(self) -> None:
        promotion = self.promotion_fixture()
        promotion["authority"]["mayAuthorizeImplementation"] = True

        validation = validate_local_promotion_artifact(promotion)

        self.assertFalse(validation["ok"])
        self.assertEqual(validation["errors"][0]["code"], "NOTEBOOKLM_LOCAL_PROMOTION_AUTHORITY_INVALID")


if __name__ == "__main__":
    unittest.main()
