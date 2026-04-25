# NotebookLM promotion-blocking tests status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-promotion-blocking-tests`

## Goal

Add promotion-blocking tests proving that captured NotebookLM provider results cannot enter executor context or patch authority without a separate local promotion artifact.

## Result

Added:

- `polyglot-mini/polyglot/notebooklm_promotion_policy.py`
- `polyglot-mini/tests/test_notebooklm_promotion_policy.py`
- `docs/contracts/notebooklm-promotion-blocking.md`
- `docs/schemas/notebooklm-promotion-decision-v0.json`
- generated block-decision fixtures under `artifacts/manual-gated/notebooklm/promotion-blocking-fixture/`

## Behavior

A captured NotebookLM ProviderResult is blocked by default from:

- executor context
- patch authority

A local promotion artifact can allow executor context only when locally verified and target-specific. It does not imply patch authority.

## Next lane

Wire the promotion policy into dossier/provider-output paths so NotebookLM provider evidence remains planner-only until explicitly promoted.
