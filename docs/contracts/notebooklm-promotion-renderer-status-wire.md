# NotebookLM Promotion Renderer Status Wire

Date: 2026-04-25  
Status: local status wiring, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract wires rendered NotebookLM promotion decisions into the human-facing status surface.

The status cockpit now reports rendered promotion-decision Markdown documents, and the current-state docs point to the rendered executor-context and patch-authority block decisions.

## Behavior

The cockpit reports:

- rendered promotion-decision Markdown count,
- rendered promotion-decision Markdown paths.

The docs point to:

- `artifacts/manual-gated/notebooklm/promotion-decision-renderer/executor-context-block-decision.md`
- `artifacts/manual-gated/notebooklm/promotion-decision-renderer/patch-authority-block-decision.md`

## Authority boundary

Readable status is not promotion. Rendering is not verification. Rendering is not patch authority.

```text
NotebookLM can inform; local artifacts decide.
```
