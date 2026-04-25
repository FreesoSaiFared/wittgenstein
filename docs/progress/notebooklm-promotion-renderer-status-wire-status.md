# NotebookLM promotion renderer status wire status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-promotion-renderer-status-wire`

## Goal

Wire rendered promotion decisions into the status docs and cockpit output as readable pointers.

## Result

Updated:

- `scripts/notebooklm_status_cockpit.sh`
- `docs/status/notebooklm-provider-current-state.md`
- `docs/status/notebooklm-lane-index.md`

Added:

- `polyglot-mini/tests/test_notebooklm_promotion_renderer_status_wire.py`
- `docs/contracts/notebooklm-promotion-renderer-status-wire.md`
- `docs/progress/notebooklm-promotion-renderer-status-wire-status.md`

## Behavior

Cockpit output now reports rendered promotion-decision Markdown count and paths.

No live NotebookLM operation is performed.
