from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
from typing import Mapping

NOTEBOOKLM_PROVIDER = "notebooklm"
NOTEBOOKLM_IMPORT_NAME = "notebooklm"
NOTEBOOKLM_DISTRIBUTION_NAME = "notebooklm-py"
NOTEBOOKLM_CLI_NAME = "notebooklm"
NOTEBOOKLM_STORAGE_FILENAME = "storage_state.json"


def preflight_notebooklm_provider(env: Mapping[str, str] | None = None) -> dict:
    env_map = dict(os.environ if env is None else env)

    package = _package_check()
    cli = _cli_check()
    storage = _storage_check(env_map)

    errors = []
    if not package["importable"]:
        errors.append(
            _error(
                "NOTEBOOKLM_PACKAGE_MISSING",
                "Python import 'notebooklm' is not importable in this environment.",
                details={
                    "importName": NOTEBOOKLM_IMPORT_NAME,
                    "distributionName": NOTEBOOKLM_DISTRIBUTION_NAME,
                },
            )
        )
    if not cli["available"]:
        errors.append(
            _error(
                "NOTEBOOKLM_CLI_MISSING",
                "CLI command 'notebooklm' is not available on PATH.",
                details={"cliName": NOTEBOOKLM_CLI_NAME},
            )
        )
    if storage["checked"] and not storage["exists"]:
        errors.append(
            _error(
                "NOTEBOOKLM_STORAGE_MISSING",
                "Configured NotebookLM storage/auth file is missing.",
                details={
                    "source": storage["source"],
                    "path": storage["path"],
                },
            )
        )

    errors.append(
        _error(
            "NOTEBOOKLM_AUTH_UNVERIFIED",
            "NotebookLM auth/session state was not verified because this preflight stays local-only.",
            blocking=False,
        )
    )
    errors.append(
        _error(
            "NOTEBOOKLM_READY_UNVERIFIED",
            "NotebookLM remains a provider seam until a real adapter is implemented and verified.",
        )
    )

    if not package["importable"] or not cli["available"]:
        status = "unavailable"
        reason = "NotebookLM local preflight failed required package/CLI availability checks."
    else:
        status = "not_ready"
        if storage["checked"] and not storage["exists"]:
            reason = "NotebookLM tooling is present, but the configured storage/auth path is missing and the adapter is still unwired."
        else:
            reason = "NotebookLM tooling is present, but auth readiness and real adapter execution remain unverified."

    safe_smoke_command = f"{NOTEBOOKLM_CLI_NAME} --help" if cli["available"] else None

    preflight = {
        "offlineOnly": True,
        "commandsRun": [],
        "package": package,
        "cli": cli,
        "storage": storage,
        "networkCalls": [],
        "notebooklmOperationsInvoked": [],
    }

    return {
        "provider": NOTEBOOKLM_PROVIDER,
        "status": status,
        "mode": "provider_seam",
        "reason": reason,
        "safeSmokeCommand": safe_smoke_command,
        "errors": errors,
        "preflight": preflight,
        # Backward-compatible summary fields used by dossier metadata rendering.
        "moduleChecks": [
            {
                "module": NOTEBOOKLM_IMPORT_NAME,
                "available": package["importable"],
                "origin": package.get("origin"),
            }
        ],
        "matchingDistributions": package["matchingDistributions"],
        "cliCandidates": [
            {"name": NOTEBOOKLM_CLI_NAME, "path": cli["path"]}
        ]
        if cli["available"] and cli["path"]
        else [],
    }


def _package_check() -> dict:
    spec = importlib.util.find_spec(NOTEBOOKLM_IMPORT_NAME)
    distributions = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name", "")
        if "notebooklm" not in name.lower():
            continue
        entry_points = sorted(
            entry_point.name
            for entry_point in distribution.entry_points
            if getattr(entry_point, "group", "") == "console_scripts"
        )
        distributions.append(
            {
                "name": name,
                "version": distribution.version,
                "summary": distribution.metadata.get("Summary"),
                "location": str(distribution.locate_file("")),
                "entryPoints": entry_points,
            }
        )

    return {
        "importName": NOTEBOOKLM_IMPORT_NAME,
        "distributionName": NOTEBOOKLM_DISTRIBUTION_NAME,
        "importable": spec is not None,
        "origin": getattr(spec, "origin", None) if spec else None,
        "matchingDistributions": distributions,
    }


def _cli_check() -> dict:
    path = shutil.which(NOTEBOOKLM_CLI_NAME)
    return {
        "name": NOTEBOOKLM_CLI_NAME,
        "available": bool(path),
        "path": path,
        "safeSmokeCommand": f"{NOTEBOOKLM_CLI_NAME} --help" if path else None,
    }


def _storage_check(env_map: Mapping[str, str]) -> dict:
    explicit_auth_json = env_map.get("NOTEBOOKLM_AUTH_JSON")
    if explicit_auth_json:
        path = Path(explicit_auth_json).expanduser()
        return {
            "checked": True,
            "source": "NOTEBOOKLM_AUTH_JSON",
            "path": str(path),
            "exists": path.exists(),
        }

    notebooklm_home = env_map.get("NOTEBOOKLM_HOME")
    if notebooklm_home:
        path = Path(notebooklm_home).expanduser() / NOTEBOOKLM_STORAGE_FILENAME
        return {
            "checked": True,
            "source": "NOTEBOOKLM_HOME",
            "path": str(path),
            "exists": path.exists(),
        }

    return {
        "checked": False,
        "source": None,
        "path": None,
        "exists": False,
    }


def _error(code: str, message: str, *, blocking: bool = True, details: dict | None = None) -> dict:
    return {
        "code": code,
        "message": message,
        "blocking": blocking,
        "details": details or {},
    }
