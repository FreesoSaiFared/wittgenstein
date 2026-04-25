# NotebookLM promotion policy wire status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-promotion-policy-wire`

## Goal

Wire the NotebookLM promotion policy into dossier/provider-output paths so NotebookLM provider evidence remains planner-only until explicitly promoted.

## Result

Updated dossier behavior for `provider=notebooklm`:

- records `providerMeta.promotionDecision`
- records `providerMeta.plannerOnlyUntilLocalPromotion`
- renders `## Promotion policy decision` in `provider-output.md`

Added:

- `polyglot-mini/tests/test_notebooklm_promotion_wire.py`
- `docs/contracts/notebooklm-promotion-policy-wire.md`
- `docs/progress/notebooklm-promotion-policy-wire-status.md`
- fixture decision under `artifacts/manual-gated/notebooklm/promotion-policy-wire-fixture/`

## Behavior

NotebookLM provider evidence remains blocked from executor context unless locally promoted.

## Next lane

Add a small verification command that runs all NotebookLM safety, conversion, promotion, and dossier-wire checks together.
