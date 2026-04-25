from __future__ import annotations

from typing import Any

DECISION_SCHEMA_VERSION = "notebooklm-promotion-decision-v0"
PROMOTION_SCHEMA_VERSION = "notebooklm-local-promotion-v0"
PROVIDER_RESULT_CONTRACT_VERSION = "notebooklm-provider-result-v0"


def _error(code: str, message: str, *, blocking: bool = True, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "blocking": blocking,
        "details": details or {},
    }


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
    """Decide whether NotebookLM provider evidence may be promoted locally.

    Provider evidence never promotes itself. A separate local promotion artifact is
    required before provider output can enter executor context or patch authority.
    """

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

    if promotion_artifact.get("schemaVersion") != PROMOTION_SCHEMA_VERSION:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_SCHEMA_INVALID",
                "Local promotion artifact schema is missing or unsupported.",
                details={"schemaVersion": promotion_artifact.get("schemaVersion")},
            )
        )
        return decision

    if promotion_artifact.get("provider") != "notebooklm":
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_PROVIDER_INVALID",
                "Local promotion artifact must target NotebookLM evidence.",
                details={"provider": promotion_artifact.get("provider")},
            )
        )
        return decision

    local_verification = promotion_artifact.get("localVerification", {})
    if local_verification.get("status") != "verified":
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_VERIFICATION_REQUIRED",
                "Local promotion requires an explicit verified localVerification section.",
                details={"localVerification": local_verification},
            )
        )
        return decision

    allowed_targets = set(promotion_artifact.get("allowedTargets", []))
    if target not in allowed_targets:
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_LOCAL_PROMOTION_TARGET_NOT_ALLOWED",
                "Local promotion artifact does not allow the requested target.",
                details={"target": target, "allowedTargets": sorted(allowed_targets)},
            )
        )
        return decision

    if target == "executor_context":
        decision["ok"] = True
        decision["canEnterExecutorContext"] = True
        decision["canAuthorizePatch"] = False
        decision["errors"] = []
        return decision

    if target == "patch_authority":
        if promotion_artifact.get("allowsPatchAuthority") is True:
            decision["ok"] = True
            decision["canEnterExecutorContext"] = True
            decision["canAuthorizePatch"] = True
            decision["errors"] = []
            return decision
        decision["errors"].append(
            _error(
                "NOTEBOOKLM_PATCH_AUTHORITY_NOT_GRANTED",
                "Local promotion artifact does not grant patch authority.",
                details={"allowsPatchAuthority": promotion_artifact.get("allowsPatchAuthority")},
            )
        )
        return decision

    decision["errors"].append(
        _error(
            "NOTEBOOKLM_PROMOTION_TARGET_UNKNOWN",
            "Unknown NotebookLM promotion target.",
            details={"target": target},
        )
    )
    return decision
