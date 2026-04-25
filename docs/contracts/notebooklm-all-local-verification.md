# NotebookLM All-Local Verification Command

Date: 2026-04-25  
Status: local verification, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract defines a single command for verifying the local NotebookLM safety, conversion, promotion, and dossier-wire path.

```bash
scripts/verify_notebooklm_all_local.sh
```

The command is intentionally local-only. It does not run NotebookLM, does not touch network, does not refresh auth, and does not automate a browser.

## Checks

The verifier runs:

- raw transcript hygiene,
- NotebookLM schema JSON syntax checks,
- NotebookLM artifact JSON syntax checks,
- Python compile checks for NotebookLM modules and tests,
- NotebookLM-related unit tests,
- `git diff --check`.

## Output behavior

By default the verifier writes its log and result JSON under `/tmp` so routine verification does not dirty the worktree.

A caller can set:

```bash
export WITT_NOTEBOOKLM_ALL_VERIFY_OUT=/some/path
```

## Authority boundary

Passing this verifier does not authorize implementation. It only proves the local NotebookLM evidence machinery is coherent.

```text
NotebookLM can inform; local artifacts decide.
```
