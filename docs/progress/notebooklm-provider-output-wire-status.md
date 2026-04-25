# NotebookLM provider-output wire status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-provider-output-wire`

## Goal

Wire the pure NotebookLM adapter skeleton into provider metadata and `provider-output.md` without changing NotebookLM authority or calling NotebookLM.

## Result

`provider=notebooklm` now records adapter skeleton metadata in:

- `manifest.json` under `providerMeta.adapterResult`
- `manifest.json` under `providerMeta.contractVersion`
- `manifest.json` under `providerMeta.adapterStatus`
- `provider-output.md` under `## Adapter skeleton result`

## Behavior

NotebookLM still does not succeed.

The current behavior remains:

- `unavailable` when package/CLI/preflight is missing
- `not_ready` when local tooling exists but live adapter/auth/capture is not verified
- no NotebookLM CLI command is run
- no NotebookLM Python client operation is run
- no network call is made
- no browser automation is added
- no NotebookLM output can authorize implementation

## Verification

Tests run:

```bash
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py
PYTHONPATH=polyglot-mini python3 -m polyglot.cli dossier "notebooklm provider output wire smoke" --provider notebooklm --sources polyglot-mini/polyglot/cli.py --out /tmp/notebooklm-provider-output-wire-smoke.md || true
python3 -m py_compile polyglot-mini/polyglot/dossier.py polyglot-mini/polyglot/notebooklm_adapter.py polyglot-mini/polyglot/notebooklm_provider.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py
git diff --check
```

## Next lane

Plan the first authenticated, read-only NotebookLM capture experiment behind an explicit manual gate. Do not run that experiment automatically.
