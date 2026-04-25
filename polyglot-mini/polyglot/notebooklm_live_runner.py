from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .notebooklm_redaction import redact_text

SCHEMA_VERSION = "notebooklm-live-runner-result-v0"
EXPECTED_GATE = "I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM"
EXPECTED_READONLY_ENABLE = "I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY"
EXPECTED_LIVE_ENABLE = "I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST"
EXPECTED_SUBPROCESS_ENABLE = "I_EXPLICITLY_ALLOW_THIS_PROCESS_TO_RUN_NOTEBOOKLM_LIST"
COMMAND = ("notebooklm", "list")


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[Sequence[str], Mapping[str, str]], CommandResult]


def default_command_runner(command: Sequence[str], env: Mapping[str, str]) -> CommandResult:
    completed = subprocess.run(
        list(command),
        text=True,
        capture_output=True,
        check=False,
        env=dict(env),
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _bool_env(env: Mapping[str, str], key: str) -> bool:
    return bool(env.get(key, ""))


def _error(code: str, message: str, *, blocking: bool, details: dict | None = None) -> dict:
    return {
        "code": code,
        "message": message,
        "blocking": blocking,
        "details": details or {},
    }


def evaluate_live_runner_gate(env: Mapping[str, str]) -> dict:
    operation = env.get("WITT_NOTEBOOKLM_OPERATION", "readonly-list")
    notebooklm_home = env.get("NOTEBOOKLM_HOME", "")

    state = {
        "operation": operation,
        "manualGatePresent": _bool_env(env, "WITT_NOTEBOOKLM_MANUAL_GATE"),
        "notebooklmHomePresent": bool(notebooklm_home),
        "readonlyEnablePresent": _bool_env(env, "WITT_NOTEBOOKLM_ENABLE_READONLY_LIST"),
        "liveEnablePresent": _bool_env(env, "WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION"),
        "subprocessEnablePresent": _bool_env(env, "WITT_NOTEBOOKLM_ALLOW_SUBPROCESS_EXECUTION"),
        "notebooklmHome": notebooklm_home,
        "status": "blocked",
        "ok": False,
        "mayExecute": False,
        "errors": [],
    }

    if operation != "readonly-list":
        state["status"] = "blocked"
        state["errors"].append(_error("NOTEBOOKLM_OPERATION_UNSUPPORTED", "Only readonly-list is supported.", blocking=True))
    elif env.get("WITT_NOTEBOOKLM_MANUAL_GATE") != EXPECTED_GATE:
        state["status"] = "gate_missing"
        state["errors"].append(_error("NOTEBOOKLM_MANUAL_GATE_MISSING", "Manual NotebookLM gate is missing or invalid.", blocking=True))
    elif not notebooklm_home:
        state["status"] = "home_missing"
        state["errors"].append(_error("NOTEBOOKLM_HOME_MISSING", "NOTEBOOKLM_HOME must be explicit.", blocking=True))
    elif env.get("WITT_NOTEBOOKLM_ENABLE_READONLY_LIST") != EXPECTED_READONLY_ENABLE:
        state["status"] = "readonly_enable_missing"
        state["errors"].append(_error("NOTEBOOKLM_READONLY_LIST_ENABLE_MISSING", "readonly-list enable variable is missing or invalid.", blocking=True))
    elif env.get("WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION") != EXPECTED_LIVE_ENABLE:
        state["status"] = "live_execution_disabled"
        state["ok"] = True
        state["errors"].append(_error("NOTEBOOKLM_LIVE_EXECUTION_DISABLED", "Live execution gate is absent; no command may run.", blocking=False))
    elif env.get("WITT_NOTEBOOKLM_ALLOW_SUBPROCESS_EXECUTION") != EXPECTED_SUBPROCESS_ENABLE:
        state["status"] = "subprocess_execution_disabled"
        state["ok"] = True
        state["errors"].append(_error("NOTEBOOKLM_SUBPROCESS_EXECUTION_DISABLED", "Final subprocess execution gate is absent; no command may run.", blocking=False))
    else:
        state["status"] = "ready_to_execute"
        state["ok"] = True
        state["mayExecute"] = True

    return state


def run_readonly_list_guarded(
    *,
    out_root: str | Path,
    env: Mapping[str, str] | None = None,
    command_runner: CommandRunner | None = None,
) -> dict:
    resolved_env = dict(os.environ if env is None else env)
    out_path = Path(out_root)
    out_path.mkdir(parents=True, exist_ok=True)

    gate = evaluate_live_runner_gate(resolved_env)
    command_runner = command_runner or default_command_runner

    command_txt = "notebooklm list\n"
    (out_path / "command.txt").write_text(command_txt, encoding="utf-8")

    live_executed = False
    commands_executed: list[str] = []
    returncode: int | None = None
    raw_stdout = ""
    raw_stderr = ""

    if gate["mayExecute"]:
        command_env = dict(resolved_env)
        result = command_runner(COMMAND, command_env)
        live_executed = True
        commands_executed.append("notebooklm list")
        returncode = result.returncode
        raw_stdout = result.stdout
        raw_stderr = result.stderr
        status = "readonly_probe_captured" if result.returncode == 0 else "readonly_probe_failed"
        ok = result.returncode == 0
    else:
        status = gate["status"]
        ok = bool(gate["ok"])
        raw_stdout = (
            "NOTEBOOKLM GUARDED LIVE RUNNER\n"
            f"status={status}\n"
            "liveNotebookLMExecuted=false\n"
            "No NotebookLM command was executed.\n"
        )
        raw_stderr = ""

    stdout_redacted, stdout_report = redact_text(raw_stdout)
    stderr_redacted, stderr_report = redact_text(raw_stderr)

    (out_path / "transcript.stdout.raw.txt").write_text(raw_stdout, encoding="utf-8")
    (out_path / "transcript.stderr.raw.txt").write_text(raw_stderr, encoding="utf-8")
    (out_path / "transcript.stdout.redacted.txt").write_text(stdout_redacted, encoding="utf-8")
    (out_path / "transcript.stderr.redacted.txt").write_text(stderr_redacted, encoding="utf-8")
    (out_path / "redaction-report.stdout.json").write_text(json.dumps(stdout_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_path / "redaction-report.stderr.json").write_text(json.dumps(stderr_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result_doc = {
        "schemaVersion": SCHEMA_VERSION,
        "provider": "notebooklm",
        "mode": "live_runner_guarded",
        "status": status,
        "ok": ok,
        "requestedOperation": gate["operation"],
        "command": "notebooklm list",
        "returncode": returncode,
        "liveNotebookLMExecuted": live_executed,
        "commandsExecuted": commands_executed,
        "gate": gate,
        "rawTranscriptPaths": [str(out_path / "transcript.stdout.raw.txt"), str(out_path / "transcript.stderr.raw.txt")],
        "redactedTranscriptPaths": [str(out_path / "transcript.stdout.redacted.txt"), str(out_path / "transcript.stderr.redacted.txt")],
        "redactionReportPaths": [str(out_path / "redaction-report.stdout.json"), str(out_path / "redaction-report.stderr.json")],
        "errors": gate["errors"],
        "authority": {
            "mayCreateClaims": False,
            "mayAuthorizeImplementation": False,
            "requiresLocalPromotion": True,
            "providerOutputOnly": True,
        },
    }
    (out_path / "result.json").write_text(json.dumps(result_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""# NotebookLM guarded live runner\n\nStatus: `{status}`  \nOK: `{ok}`  \nLive NotebookLM executed: `{live_executed}`  \nCommand: `notebooklm list`\n\nRaw transcript files are always routed through the local redactor before provider evidence use.\n\nNotebookLM can inform; local artifacts decide.\n"""
    (out_path / "README.md").write_text(readme, encoding="utf-8")
    return result_doc
