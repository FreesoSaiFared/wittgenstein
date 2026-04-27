# NotebookLM Read-Only Runner Gate

Date: 2026-04-25  
Status: gate-only, no live NotebookLM operation  
Provider: `notebooklm`  
Operation: `readonly-list`

## Purpose

This contract adds a gate layer between the manual capture runner skeleton and any future live read-only NotebookLM probe.

It names the required explicit enable variable for the future `readonly-list` operation while still refusing to execute NotebookLM in this lane.

## Required future gate

A future live runner may consider `readonly-list` only when all variables are exact:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

The enable variable name is intentionally specific. It should not accidentally unlock other NotebookLM operations.

## Behavior today

`scripts/notebooklm_readonly_runner_gate.sh`:

- writes local artifacts,
- classifies gate/home/enable state,
- records the future command as `notebooklm list`,
- records `liveNotebookLMExecuted: false`,
- records `commandsExecuted: []`,
- executes no NotebookLM command.

If the future gate is fully satisfied, the script returns `readonly_enabled_not_executed`. That means the gate is shaped correctly, not that NotebookLM has been touched.

## Status values

- `gate_missing`
- `home_missing`
- `blocked`
- `readonly_enabled_not_executed`

## New error codes

- `NOTEBOOKLM_OPERATION_UNSUPPORTED`
- `NOTEBOOKLM_READONLY_LIST_ENABLE_MISSING`
- `NOTEBOOKLM_CAPTURE_ABORTED_BY_POLICY`
- `NOTEBOOKLM_LIVE_EXECUTION_NOT_IMPLEMENTED`

## Authority boundary

No result from this gate may authorize implementation. The gate is control-plane evidence only.

```text
NotebookLM can inform; local artifacts decide.
```
