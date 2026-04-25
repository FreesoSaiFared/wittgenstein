# NotebookLM Safety Verification Gate

Date: 2026-04-25  
Status: local safety verification, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract defines the local safety verification gate that must pass before any future live NotebookLM probe is attempted.

It bundles the checks that were previously scattered across lanes into one executable safety path.

## Gate script

```bash
scripts/verify_notebooklm_safety.sh
```

The script performs local checks only. It does not run NotebookLM, does not touch network, does not refresh auth, and does not automate a browser.

## Checks

The gate runs:

1. `scripts/check_notebooklm_raw_transcripts.sh`
2. JSON syntax validation for `docs/schemas/notebooklm-*.json`
3. NotebookLM-related unit tests
4. `git diff --check`

## Required before live probe

Before any future live `notebooklm list` probe, this verification gate should pass in the same worktree that will run the probe.

The intended order is:

```text
safety verification -> explicit human gate -> one read-only command -> redaction -> provider evidence -> local promotion only if needed
```

## Authority boundary

Passing this gate does not authorize implementation. It only proves the local NotebookLM safety machinery is internally coherent.

```text
NotebookLM can inform; local artifacts decide.
```
