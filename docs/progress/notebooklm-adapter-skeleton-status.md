# NotebookLM adapter skeleton status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-adapter-skeleton`

## Goal

Add a pure local NotebookLM adapter skeleton matching `notebooklm-provider-result-v0` without performing any real NotebookLM operation.

## Result

Added `polyglot-mini/polyglot/notebooklm_adapter.py` with:

- `build_notebooklm_provider_request(...)`
- `build_notebooklm_not_ready_result(...)`
- `run_notebooklm_provider_adapter(...)`

The skeleton returns a structured `not_ready` ProviderResult with `NOTEBOOKLM_ADAPTER_NOT_WIRED` and does not call NotebookLM.

## Authority boundary

The skeleton result explicitly states:

- `mayCreateClaims: false`
- `mayAuthorizeImplementation: false`
- `requiresLocalPromotion: true`
- `providerOutputOnly: true`

## Verification

Tests run:

```bash
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py
python3 -m py_compile polyglot-mini/polyglot/notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_adapter.py
git diff --check
```

## Next lane

Wire the skeleton result into NotebookLM provider metadata/provider-output while preserving `provider=notebooklm` as failed/not-ready until live capture is explicitly verified.
