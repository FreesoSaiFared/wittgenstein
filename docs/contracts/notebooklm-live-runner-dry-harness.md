# NotebookLM Live Runner Dry Harness

Date: 2026-04-25  
Status: dry harness, no live NotebookLM operation  
Provider: `notebooklm`  
Future operation: `readonly-list`

## Purpose

This contract defines the final dry-run safety layer before a possible future one-command live read-only NotebookLM probe.

It records the exact command that a later lane may execute:

```bash
notebooklm list
```

This lane still does not execute that command.

## Full future gate

A future live runner may execute `notebooklm list` only when all variables are exact:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION=I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

The dry harness validates this shape but never runs NotebookLM.

## Behavior today

`scripts/notebooklm_live_runner_dry_harness.sh`:

- writes local artifacts,
- records the future command in `command.txt`,
- classifies gate state,
- records `liveNotebookLMExecuted: false`,
- records `commandsExecuted: []`,
- executes no NotebookLM command.

If every gate is satisfied, the status is `would_execute_but_stubbed`.

That means the future execution gate is shaped correctly. It does not mean NotebookLM was touched.

## Status values

- `gate_missing`
- `home_missing`
- `readonly_enable_missing`
- `live_execution_disabled`
- `would_execute_but_stubbed`
- `blocked`

## Error codes

- `NOTEBOOKLM_OPERATION_UNSUPPORTED`
- `NOTEBOOKLM_MANUAL_GATE_MISSING`
- `NOTEBOOKLM_HOME_MISSING`
- `NOTEBOOKLM_READONLY_LIST_ENABLE_MISSING`
- `NOTEBOOKLM_LIVE_EXECUTION_DISABLED`
- `NOTEBOOKLM_LIVE_EXECUTION_STUBBED`

## Authority boundary

Even a future successful `notebooklm list` capture would be provider evidence only.

It must not directly create implementation facts, execution-verified facts, patch authority, or promotion authority.

```text
NotebookLM can inform; local artifacts decide.
```
