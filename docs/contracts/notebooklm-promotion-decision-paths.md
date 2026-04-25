# NotebookLM Promotion Decision Paths Command

Date: 2026-04-25  
Status: local inspection command, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract adds a tiny shell-friendly command that prints rendered NotebookLM promotion-decision Markdown paths.

```bash
scripts/list_notebooklm_promotion_decisions.sh
scripts/list_notebooklm_promotion_decisions.sh --json
```

## Behavior

The command lists rendered promotion decision documents under:

```text
artifacts/manual-gated/notebooklm/promotion-decision-renderer/
```

It has two modes:

- `--text`, the default, for quick terminal inspection,
- `--json`, for structured tooling.

## Authority boundary

Listing rendered decision paths is not promotion. It is not verification. It is not patch authority.

```text
NotebookLM can inform; local artifacts decide.
```
