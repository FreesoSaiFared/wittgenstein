# NotebookLM promotion decision paths status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-promotion-decision-paths`

## Goal

Add a tiny local command to print rendered promotion decision paths only, for shell-friendly inspection.

## Result

Added:

- `scripts/list_notebooklm_promotion_decisions.sh`
- `polyglot-mini/tests/test_notebooklm_promotion_decision_paths.py`
- `docs/contracts/notebooklm-promotion-decision-paths.md`
- `docs/progress/notebooklm-promotion-decision-paths-status.md`
- fixture output under `artifacts/manual-gated/notebooklm/promotion-decision-paths/`

## Behavior

The command prints rendered promotion-decision Markdown paths in text or JSON form.

No live NotebookLM operation is performed.
No authority is granted.

## Next lane

Add a compact final NotebookLM local readiness checkpoint that references cockpit, path listing, and promotion boundaries.
