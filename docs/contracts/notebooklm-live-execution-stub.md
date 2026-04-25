# NotebookLM Live Execution Stub

Date: 2026-04-25  
Status: execution stub, no live NotebookLM operation  
Provider: `notebooklm`  
Future operation: `readonly-list`

## Purpose

This contract defines the final local stub before a possible future one-command live read-only NotebookLM probe.

The stub proves the transcript path:

```text
raw transcript -> redaction utility -> redacted transcript + redaction report -> provider evidence
```

This lane still does not execute NotebookLM.

## Future command

The only future command represented by this stub is:

```bash
notebooklm list
```

## Behavior today

`scripts/notebooklm_live_execution_stub.sh`:

- validates the future gate shape,
- records the future command in `command.txt`,
- writes stub raw stdout/stderr transcript files,
- routes both stub transcript files through `scripts/notebooklm_redact_transcript.py`,
- writes redacted transcripts and redaction reports,
- records `liveNotebookLMExecuted: false`,
- records `commandsExecuted: []`,
- executes no NotebookLM command.

## Required future gate

A later live runner may execute `notebooklm list` only when all variables are exact:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION=I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

This stub validates that shape but never runs NotebookLM.

## Status values

- `gate_missing`
- `home_missing`
- `readonly_enable_missing`
- `live_execution_disabled`
- `stubbed_transcript_redacted`
- `blocked`

## Authority boundary

A redacted transcript is still provider evidence only.

It must not directly create implementation facts, execution-verified facts, patch authority, or promotion authority.

```text
NotebookLM can inform; local artifacts decide.
```
