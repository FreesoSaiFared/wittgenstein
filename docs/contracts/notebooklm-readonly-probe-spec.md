# NotebookLM Read-Only Probe Spec

Date: 2026-04-25  
Status: spec-only, no live NotebookLM operation  
Provider: `notebooklm`  
Future operation name: `readonly-list`

## Purpose

This spec names the first future read-only NotebookLM operation for a later manually approved authenticated capture experiment.

The named future operation is:

```text
readonly-list
```

The intended future runtime equivalent is a notebook listing probe, likely `notebooklm list`, but this lane does **not** run it.

## Current boundary

This lane does not:

- run `notebooklm`
- log in
- list notebooks
- ask NotebookLM questions
- upload sources
- create or delete notebooks
- refresh auth
- use browser automation
- call `NotebookLMClient`

It only defines the spec and writes dry-run artifacts.

## Future gate requirements

A later lane may execute the read-only probe only when all of these are true:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export WITT_NOTEBOOKLM_EXPERIMENT_ID=manual-auth-capture-YYYYMMDD-HHMMSS
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

Even with those variables set, the script added in this lane remains spec-only and executes no live operation.

## Allowed future read-only operation

Only one operation is named for future approval:

| Operation | Intended future command | Mutates NotebookLM? | Approved now? |
|---|---|---:|---:|
| `readonly-list` | `notebooklm list` | No, expected read-only | No |

The future lane must verify again that `notebooklm list` is read-only before executing it.

## Required future capture artifacts

A future live probe should write:

```text
artifacts/manual-gated/notebooklm/<experiment-id>/
  request.json
  preflight.json
  command.txt
  transcript.stdout.txt
  transcript.stderr.txt
  exit-code.txt
  redaction-report.json
  result.json
  README.md
```

## Redaction requirements

Any transcript must be redacted before being committed or fed into dossier artifacts.

Redact:

- cookies
- bearer tokens
- OAuth tokens
- CSRF tokens
- session IDs
- long opaque credential-like strings
- nonessential account identifiers

Default rule: if unsure, redact.

## Expected result classification

The future live probe should classify outcomes as one of:

- `readonly_probe_captured`
- `readonly_probe_failed`
- `auth_missing`
- `auth_invalid`
- `operation_blocked`
- `redaction_required`

## Authority boundary

A successful future read-only probe can only produce provider evidence.

It cannot directly create implementation facts, execution-verified facts, patch authority, or promotion authority.

```text
NotebookLM can inform; local artifacts decide.
```
