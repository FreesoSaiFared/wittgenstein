# NotebookLM manual capture runner skeleton status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-manual-capture-runner-skeleton`

## Goal

Add a manual-gated capture runner skeleton that still refuses live NotebookLM operations.

## Result

Added:

- `docs/contracts/notebooklm-manual-capture-runner.md`
- `docs/schemas/notebooklm-manual-capture-runner-result-v0.json`
- `scripts/notebooklm_manual_capture_runner.sh`
- `docs/progress/notebooklm-manual-capture-runner-skeleton-status.md`

## Behavior

The runner writes local artifacts and classifies gate/home/operation state.

It does not execute NotebookLM, does not import the NotebookLM client, does not use network, and does not automate a browser.

## Verification

Tests run:

```bash
bash -n scripts/notebooklm_manual_capture_runner.sh
./scripts/notebooklm_manual_capture_runner.sh || test $? -eq 2
WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home WITT_NOTEBOOKLM_OPERATION=plan-only ./scripts/notebooklm_manual_capture_runner.sh
python3 -m json.tool docs/schemas/notebooklm-manual-capture-runner-result-v0.json >/dev/null
python3 -m json.tool artifacts/manual-gated/notebooklm/manual-capture-runner-dry-run/result.json >/dev/null
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py
git diff --check
```

## Next lane

Add a manual-gated read-only probe spec. It should name exactly one future read-only operation and still not execute it automatically.
