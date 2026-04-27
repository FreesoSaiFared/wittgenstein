# NotebookLM Manual Capture Runner Skeleton

Date: 2026-04-25  
Status: runner skeleton, no live NotebookLM operation  
Provider: `notebooklm`  
Related plan: `docs/contracts/notebooklm-manual-authenticated-capture-plan.md`

## Purpose

This document defines the first manual-gated capture runner skeleton for NotebookLM.

The runner exists so future lanes can add exactly one explicitly approved read-only NotebookLM operation without improvising safety logic at runtime.

This skeleton does **not** run NotebookLM. It does not log in, list notebooks, ask questions, upload sources, create notebooks, delete notebooks, refresh auth, or automate a browser.

## Rule

```text
A gate may allow the runner to prepare, but this skeleton still refuses live operations.
```

The current runner writes local artifacts only.

## Required future gate

A future live read-only probe must require all of the following:

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_EXPERIMENT_ID=manual-auth-capture-YYYYMMDD-HHMMSS
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
export WITT_NOTEBOOKLM_OPERATION=readonly-list
```

This lane does not enable `readonly-list`. Any requested live operation is classified as policy-blocked.

## Runner behavior today

The skeleton runner may:

- create a local run directory
- write `request.json`
- write `result.json`
- write `README.md`
- classify missing gate / missing home / requested operation
- report that live operations are disabled

The skeleton runner must not:

- execute `notebooklm`
- import and call `NotebookLMClient`
- touch network
- perform browser automation
- read or write real NotebookLM notebooks
- treat captured output as implementation authority

## Result statuses

| Status | Meaning |
|---|---|
| `plan_only` | Local skeleton artifact was written. |
| `blocked` | A live operation was requested but this skeleton forbids it. |
| `gate_missing` | The manual gate was not present. |
| `home_missing` | `NOTEBOOKLM_HOME` was not provided. |

## Error codes

- `NOTEBOOKLM_MANUAL_GATE_MISSING`
- `NOTEBOOKLM_HOME_MISSING`
- `NOTEBOOKLM_LIVE_OPERATION_DISABLED`
- `NOTEBOOKLM_CAPTURE_ABORTED_BY_POLICY`

## Authority boundary

Runner results are provider-planning artifacts only.

They may not create implementation facts, patch authority, or execution-verified facts.

```text
NotebookLM can inform; local artifacts decide.
```
