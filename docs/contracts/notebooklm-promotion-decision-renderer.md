# NotebookLM Promotion Decision Renderer

Date: 2026-04-25  
Status: local renderer, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract adds a tiny local renderer for NotebookLM promotion decisions.

The renderer turns promotion-decision JSON into Markdown so a human can inspect the boundary without opening raw JSON.

## Command

```bash
scripts/render_notebooklm_promotion_decision.py --input DECISION.json --output DECISION.md
```

## Authority boundary

Rendering is not promotion. Rendering is not verification. Rendering is not patch authority.

```text
NotebookLM can inform; local artifacts decide.
```
