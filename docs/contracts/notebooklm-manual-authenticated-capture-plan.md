# NotebookLM Manual-Gated Authenticated Capture Plan

Date: 2026-04-25  
Status: plan-only, manual-gated, no live NotebookLM operation  
Provider: `notebooklm`  
Related contract: `notebooklm-provider-result-v0`

## Purpose

This document defines the first safe plan for a future authenticated NotebookLM capture experiment.

This lane does **not** run NotebookLM, does **not** log in, does **not** list notebooks, does **not** create or delete notebooks, does **not** ask questions, and does **not** upload sources.

It only prepares the explicit manual gate, expected transcript shape, artifact paths, rollback notes, and safety rules for a later human-triggered experiment.

## Boundary

NotebookLM remains a provider seam, not a core codec and not an implementation-authority path.

The experiment may eventually capture NotebookLM output as provider evidence only. Captured provider evidence must still go through local promotion before it can influence implementation.

```text
NotebookLM can inform; local artifacts decide.
```

## Manual gate principle

A future authenticated capture may run only when a human explicitly sets a manual gate for that one run.

Required future environment variables:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_EXPERIMENT_ID=manual-auth-capture-YYYYMMDD-HHMMSS
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

The current planning script in this PR does **not** perform live capture even when these variables are set. It only prints and validates the planned gate shape.

## Future experiment phases

### Phase 0: Local readiness only

Allowed:

- verify repo is clean
- verify isolated venv exists
- verify `notebooklm --help`
- verify `NOTEBOOKLM_HOME` is explicit
- verify output directory exists under `/tmp` or `artifacts/manual-gated/`

Forbidden:

- `notebooklm login`
- `notebooklm list`
- `notebooklm ask`
- any notebook mutation
- any source upload
- browser automation

### Phase 1: Manual auth presence check

Allowed only in a later lane after explicit human approval:

- inspect whether `NOTEBOOKLM_HOME/storage_state.json` exists
- classify missing storage as `NOTEBOOKLM_STORAGE_MISSING`
- classify invalid/empty storage as `NOTEBOOKLM_AUTH_STORAGE_INVALID`

Still forbidden:

- token refresh
- NotebookLM network calls
- notebook operations

### Phase 2: Read-only authenticated probe

Allowed only in a later lane after a second explicit human approval:

- one read-only command or Python API call chosen from documented surface
- capture stdout/stderr/exit code
- redact secrets
- write transcript

Candidate operation, not yet approved:

```bash
notebooklm list
```

This is not approved in this lane.

### Phase 3: ProviderResult capture

If a read-only probe is successful, convert the transcript into a ProviderResult-style artifact. `ok: true` would mean provider capture succeeded. It would **not** mean the captured output is implementation authority.

## Artifact layout

Future gated runs should write under:

```text
artifacts/manual-gated/notebooklm/<experiment-id>/
  request.json
  preflight.json
  transcript.stdout.txt
  transcript.stderr.txt
  result.json
  redaction-report.json
  README.md
```

## Redaction rules

Before any transcript is committed or copied into project artifacts, redact cookies, bearer tokens, OAuth tokens, session IDs, CSRF tokens, long opaque credential-like strings, and nonessential account identifiers.

Default rule: if unsure, redact.

## Failure taxonomy additions

- `NOTEBOOKLM_MANUAL_GATE_MISSING`
- `NOTEBOOKLM_MANUAL_GATE_INVALID`
- `NOTEBOOKLM_AUTH_STORAGE_INVALID`
- `NOTEBOOKLM_READONLY_PROBE_FAILED`
- `NOTEBOOKLM_TRANSCRIPT_REDACTED`
- `NOTEBOOKLM_CAPTURE_ABORTED_BY_POLICY`

## Decision

NotebookLM can inform; local artifacts decide.
