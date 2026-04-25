from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .notebooklm_provider import preflight_notebooklm_provider

CONTRACT_VERSION = "notebooklm-provider-result-v0"
ADAPTER_NAME = "notebooklm"
ADAPTER_STATUS_NOT_READY = "not_ready"
ADAPTER_ERROR_NOT_WIRED = "NOTEBOOKLM_ADAPTER_NOT_WIRED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_notebooklm_provider_request(
    *,
    task: str,
    run_id: str,
    workspace_root: str | Path,
    working_directory: str | Path,
    base_git_sha: str | None = None,
    base_source_snapshot: str | None = None,
    source_ledger_path: str | Path | None = None,
    claim_ledger_path: str | Path | None = None,
    requested_out_path: str | Path | None = None,
    extra_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a local, metadata-only NotebookLM provider request.

    This object is deliberately not a NotebookLM runtime call. It describes what a
    future adapter may receive. It must not contain arbitrary source text unless a
    later lane explicitly adds source transfer rules.
    """

    constraints: dict[str, Any] = {
        "noImplementationAuthority": True,
        "offlineReplayRequired": True,
        "allowNotebookMutation": False,
        "allowNotebookCreation": False,
        "allowNotebookDeletion": False,
        "allowSourceUpload": False,
    }
    if extra_constraints:
        constraints.update(extra_constraints)

    return {
        "contractVersion": CONTRACT_VERSION,
        "provider": ADAPTER_NAME,
        "requestId": f"nblm-req-{uuid4().hex[:12]}",
        "runId": run_id,
        "task": task,
        "workspaceRoot": str(Path(workspace_root)),
        "workingDirectory": str(Path(working_directory)),
        "baseGitSha": base_git_sha,
        "baseSourceSnapshot": base_source_snapshot,
        "sourceLedgerPath": str(source_ledger_path) if source_ledger_path is not None else None,
        "claimLedgerPath": str(claim_ledger_path) if claim_ledger_path is not None else None,
        "requestedOutPath": str(requested_out_path) if requested_out_path is not None else None,
        "constraints": constraints,
        "createdAt": utc_now(),
    }


def build_notebooklm_not_ready_result(
    *,
    request: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    message: str = "NotebookLM adapter skeleton is present but live capture is not wired.",
) -> dict[str, Any]:
    errors = []
    if preflight:
        errors.extend(preflight.get("errors", []))
    errors.append(
        {
            "code": ADAPTER_ERROR_NOT_WIRED,
            "message": message,
            "details": {
                "adapter": "skeleton",
                "liveNotebookLMCalls": False,
                "browserAutomation": False,
            },
        }
    )

    return {
        "contractVersion": CONTRACT_VERSION,
        "provider": ADAPTER_NAME,
        "status": ADAPTER_STATUS_NOT_READY,
        "ok": False,
        "runId": request.get("runId") if request else None,
        "requestId": request.get("requestId") if request else None,
        "createdAt": utc_now(),
        "preflight": preflight or {},
        "capture": {
            "mode": "none",
            "notebookId": None,
            "notebookTitle": None,
            "operation": None,
            "capturedAt": None,
            "rawTextPath": None,
            "metadataPath": None,
        },
        "errors": errors,
        "authority": {
            "mayCreateClaims": False,
            "mayAuthorizeImplementation": False,
            "requiresLocalPromotion": True,
            "providerOutputOnly": True,
        },
    }


def run_notebooklm_provider_adapter(
    *,
    request: dict[str, Any],
    preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the current local skeleton result without calling NotebookLM.

    This function intentionally performs no subprocess, no network request, no
    NotebookLM CLI command, and no NotebookLM Python-client call. It gives dossier
    code a stable ProviderResult shape before the authenticated capture lane.
    """

    resolved_preflight = preflight if preflight is not None else preflight_notebooklm_provider()
    return build_notebooklm_not_ready_result(request=request, preflight=resolved_preflight)
