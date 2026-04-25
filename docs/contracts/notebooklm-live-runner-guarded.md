# NotebookLM Guarded Live Runner

Date: 2026-04-25  
Status: implementation guarded, tests use injected fake runner only  
Provider: `notebooklm`  
Operation: `readonly-list`

## Purpose

This contract introduces the guarded live runner shape for the future one-command NotebookLM read-only probe.

The runner can execute `notebooklm list` only if every gate is present, including a final subprocess-specific gate:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION=I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST
export WITT_NOTEBOOKLM_ALLOW_SUBPROCESS_EXECUTION=I_EXPLICITLY_ALLOW_THIS_PROCESS_TO_RUN_NOTEBOOKLM_LIST
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

This lane does **not** run real NotebookLM. Tests use an injected fake command runner.

## Transcript route

All stdout/stderr is written raw and then immediately routed through the redactor:

```text
subprocess stdout/stderr -> raw transcript files -> redaction -> redacted transcript files + reports -> result.json
```

## Safety rule

Without the final subprocess gate, even the live-enable gate is insufficient.

This makes accidental execution through copied environment variables less likely.

## Authority boundary

A successful future `notebooklm list` capture would still be provider evidence only.

```text
NotebookLM can inform; local artifacts decide.
```
