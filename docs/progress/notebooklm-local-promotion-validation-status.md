# NotebookLM local promotion validation status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-local-promotion-validation`

## Goal

Tighten local promotion validation into code-level schema checks before any provider result can be locally promoted.

## Result

Added:

- `validate_local_promotion_artifact(...)` in `polyglot-mini/polyglot/notebooklm_promotion_policy.py`
- `polyglot-mini/tests/test_notebooklm_promotion_validation.py`
- `docs/schemas/notebooklm-local-promotion-validation-v0.json`
- `docs/contracts/notebooklm-local-promotion-validation.md`
- validation fixtures under `artifacts/manual-gated/notebooklm/local-promotion-validation/`

Updated:

- `scripts/verify_notebooklm_all_local.sh` now runs all NotebookLM tests dynamically.
- `scripts/verify_notebooklm_safety.sh` now runs all NotebookLM tests dynamically.

## Behavior

Promotion artifacts now fail closed when malformed or too broad.
Patch authority smuggling is explicitly rejected.

## Next lane

Add a tiny promotion-decision renderer so local promotion decisions can be inspected without opening raw JSON.
