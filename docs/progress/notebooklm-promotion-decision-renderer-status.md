# NotebookLM promotion decision renderer status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-promotion-decision-renderer`

## Goal

Add a tiny promotion-decision renderer so local promotion decisions can be inspected without opening raw JSON.

## Result

Added:

- `polyglot-mini/polyglot/notebooklm_promotion_render.py`
- `scripts/render_notebooklm_promotion_decision.py`
- `polyglot-mini/tests/test_notebooklm_promotion_render.py`
- `docs/contracts/notebooklm-promotion-decision-renderer.md`
- rendered fixtures under `artifacts/manual-gated/notebooklm/promotion-decision-renderer/`

## Behavior

The renderer converts promotion-decision JSON into Markdown.
It executes no NotebookLM command.
It grants no authority.

## Next lane

Wire rendered promotion decisions into the status docs or cockpit output as a readable pointer.
