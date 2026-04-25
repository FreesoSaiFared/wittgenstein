from __future__ import annotations

from typing import Any

DECISION_SCHEMA_VERSION = "notebooklm-promotion-decision-v0"
PROMOTION_SCHEMA_VERSION = "notebooklm-local-promotion-v0"
PROMOTION_VALIDATION_SCHEMA_VERSION = "notebooklm-local-promotion-validation-v0"
PROVIDER_RESULT_CONTRACT_VERSION = "notebooklm-provider-result-v0"
ALLOWED_PROMOTION_TARGETS = {"planner_context", "executor_context"}
REQUIRED_AUTHORITY = {
    "mayCreateClaims": False,
    "mayAuthorizeImplementation": False,
    "mayAuthorizePatch": False,
    "providerOutputOnly": True,
    "requiresLocalPromotion": False,
}


def _error(code: str, message: str, *, blocking: bool = True, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "blocking": blocking,
        "details": details or {},
    }


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_local_promotion_artifact(promotion_artifact: dict[str, Any] | None) -> dict[str, Any]:
    """Validate the local NotebookLM promotion artifact shape without external deps."""

    validation = {
        "schemaVersion": PROMOTION_VALIDATION_SCHEMA_VERSION,
        "provider": "notebooklm",
        "ok": False,
        "allowedTargets": [],
        "allowsPatchAuthority": None,
        "errors": [],
    }

    if not isinstance(promotion_artifact, dict):
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_NOT_OBJECT",
                "Local promotion artifact must be a JSON object.",
            )
        )
        return validation

    if promotion_artifact.get("schemaVersion") != PROMOTION_SCHEMA_VERSION:
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_SCHEMA_VERSION_INVALID",
                "Local promotion artifact schema version is missing or unsupported.",
                details={"schemaVersion": promotion_artifact.get("schemaVersion")},
            )
        )

    if promotion_artifact.get("provider") != "notebooklm":
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_PROVIDER_INVALID",
                "Local promotion artifact must target NotebookLM evidence.",
                details={"provider": promotion_artifact.get("provider")},
            )
        )

    if promotion_artifact.get("sourceProviderResultContractVersion") != PROVIDER_RESULT_CONTRACT_VERSION:
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_SOURCE_CONTRACT_INVALID",
                "Local promotion artifact must reference the NotebookLM provider result contract.",
                details={"sourceProviderResultContractVersion": promotion_artifact.get("sourceProviderResultContractVersion")},
            )
        )

    allowed_targets = promotion_artifact.get("allowedTargets")
    if not isinstance(allowed_targets, list) or not allowed_targets:
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_TARGETS_INVALID",
                "Local promotion artifact must include a non-empty allowedTargets list.",
                details={"allowedTargets": allowed_targets},
            )
        )
    else:
        seen: list[str] = []
        for target in allowed_targets:
            if target not in ALLOWED_PROMOTION_TARGETS:
                validation["errors"].append(
                    _error(
                        "NOTEBOOKLM_LOCAL_PROMOTION_TARGET_INVALID",
                        "Local promotion artifact contains an unsupported target.",
                        details={"target": target, "allowedTargets": sorted(ALLOWED_PROMOTION_TARGETS)},
                    )
                )
            elif target not in seen:
                seen.append(target)
        validation["allowedTargets"] = seen

    allows_patch_authority = promotion_artifact.get("allowsPatchAuthority")
    validation["allowsPatchAuthority"] = allows_patch_authority
    if allows_patch_authority is not False:
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_PATCH_AUTHORITY_FORBIDDEN",
                "NotebookLM local promotion v0 must not grant patch authority.",
                details={"allowsPatchAuthority": allows_patch_authority},
            )
        )

    local_verification = promotion_artifact.get("localVerification")
    if not isinstance(local_verification, dict):
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_VERIFICATION_OBJECT_REQUIRED",
                "Local promotion artifact must include a localVerification object.",
            )
        )
    else:
        if local_verification.get("status") != "verified":
            validation["errors"].append(
                _error(
                    "NOTEBOOKLM_LOCAL_VERIFICATION_REQUIRED",
                    "Local promotion requires localVerification.status=verified.",
                    details={"localVerification": local_verification},
                )
            )
        if not _nonempty_string(local_verification.get("method")):
            validation["errors"].append(
                _error(
                    "NOTEBOOKLM_LOCAL_VERIFICATION_METHOD_REQUIRED",
                    "Local promotion requires a non-empty verification method.",
                )
            )
        if not _nonempty_string(local_verification.get("verifiedBy")):
            validation["errors"].append(
                _error(
                    "NOTEBOOKLM_LOCAL_VERIFICATION_ACTOR_REQUIRED",
                    "Local promotion requires a non-empty verifiedBy field.",
                )
            )

    authority = promotion_artifact.get("authority")
    if not isinstance(authority, dict):
        validation["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_AUTHORITY_REQUIRED",
                "Local promotion artifact must include authority boundary fields.",
            )
        )
    else:
        for key, expected in REQUIRED_AUTHORITY.items():
            if authority.get(key) is not expected:
                validation["errors"].append(
                    _error(
                        "NOTEBOOKLM_LOCAL_PROMOTION_AUTHORITY_INVALID",
                        "Local promotion authority boundary is too broad or malformed.",
                        details={"field": key, "expected": expected, "actual": authority.get(key)},
                    )
                )

    validation["ok"] = not validation["errors"]
    return validation


def _base_decision(*, target: str, provider_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": DECISION_SCHEMA_VERSION,
        "provider": "notebooklm",
        "target": target,
        "ok": False,
        "canEnterExecutorContext": False,
        "canAuthorizePatch": False,
        "providerResultStatus": provider_result.get("status"),
        "providerResultOk": provider_result.get("ok"),
        "providerOutputOnly": provider_result.get("authority", {}).get("providerOutputOnly"),
        "requiresLocalPromotion": True,
        "localPromotionValidation": None,
        "errors": [],
        "authority": {
            "providerMayCreateClaims": False,
            "providerMayAuthorizeImplementation": False,
            "localPromotionRequired": True,
        },
    }


def evaluate_notebooklm_provider_promotion(
    provider_result: dict[str, Any],
    *,
    promotion_artifact: dict[str, Any] | None = None,
    target: str = "executor_context",
) -> dict[str, Any]:
    """Decide whether NotebookLM provider evidence may be promoted locally."""

    decision = _base_decision(target=target, provider_result=provider_result)

    if provider_result.get("provider") != "notebooklm":
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_PROVIDER_RESULT_REQUIRED",
                "Promotion policy only accepts NotebookLM provider results.",
                details={"provider": provider_result.get("provider")},
            )
        )
        return decision

    if provider_result.get("contractVersion") != PROVIDER_RESULT_CONTRACT_VERSION:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_PROVIDER_RESULT_CONTRACT_INVALID",
                "NotebookLM provider result contract version is missing or unsupported.",
                details={"contractVersion": provider_result.get("contractVersion")},
            )
        )
        return decision

    if provider_result.get("status") != "captured" or provider_result.get("ok") is not True:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_PROVIDER_RESULT_NOT_CAPTURED",
                "NotebookLM provider result is not captured/ok, so it cannot be promoted.",
                details={"status": provider_result.get("status"), "ok": provider_result.get("ok")},
            )
        )
        return decision

    provider_authority = provider_result.get("authority", {})
    if provider_authority.get("mayCreateClaims") is not False or provider_authority.get("mayAuthorizeImplementation") is not False:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_PROVIDER_AUTHORITY_TOO_BROAD",
                "NotebookLM provider result claims authority it must not have.",
                details={"authority": provider_authority},
            )
        )
        return decision

    if promotion_artifact is None:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_REQUIRED",
                "Captured NotebookLM provider evidence cannot enter executor context or patch authority without a separate local promotion artifact.",
            )
        )
        return decision

    validation = validate_local_promotion_artifact(promotion_artifact)
    decision["localPromotionValidation"] = validation
    if not validation["ok"]:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_SCHEMA_INVALID",
                "Local promotion artifact failed code-level validation.",
                details={"validationErrors": validation["errors"]},
            )
        )
        return decision

    allowed_targets = set(validation["allowedTargets"])
    if target not in allowed_targets:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_TARGET_NOT_ALLOWED",
                "Local promotion artifact does not allow the requested target.",
                details={"target": target, "allowedTargets": sorted(allowed_targets)},
            )
        )
        return decision

    if target == "planner_context":
        decision["ok"] = True
        decision["canEnterExecutorContext"] = False
        decision["canAuthorizePatch"] = False
        decision["errors"] = []
        return decision

    if target == "executor_context":
        decision["ok"] = True
        decision["canEnterExecutorContext"] = True
        decision["canAuthorizePatch"] = False
        decision["errors"] = []
        return decision

    decision["errors"].append(
        _error(
            "NOTEBOOKLM_PROMOTION_TARGET_UNKNOWN",
            "Unknown NotebookLM promotion target.",
            details={"target": target},
        )
    )
    return decision
