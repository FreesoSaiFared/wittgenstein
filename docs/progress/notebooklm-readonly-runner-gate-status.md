# NotebookLM readonly runner gate status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-readonly-runner-gate`

## Goal

Add a gated runner mode for `readonly-list` that still defaults to policy-blocked unless a future explicit enable variable is present.

## Result

Added:

- `scripts/notebooklm_readonly_runner_gate.sh`
- `docs/contracts/notebooklm-readonly-runner-gate.md`
- `docs/progress/notebooklm-readonly-runner-gate-status.md`
- dry-run artifacts under `artifacts/manual-gated/notebooklm/readonly-runner-gate-dry-run/`

## Behavior

The script never runs NotebookLM.

It classifies:

- missing/invalid manual gate,
- missing `NOTEBOOKLM_HOME`,
- missing readonly-list enable variable,
- fully shaped gate that is still not executed.

## Verification

Tests run:

```bash
bash -n scripts/notebooklm_readonly_runner_gate.sh
./scripts/notebooklm_readonly_runner_gate.sh || test $? -eq 2
WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home WITT_NOTEBOOKLM_OPERATION=readonly-list ./scripts/notebooklm_readonly_runner_gate.sh || test $? -eq 2
WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home WITT_NOTEBOOKLM_OPERATION=readonly-list ./scripts/notebooklm_readonly_runner_gate.sh
python3 -m json.tool artifacts/manual-gated/notebooklm/readonly-runner-gate-dry-run/result.json >/dev/null
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py
git diff --check
```

## Next lane

Add the live-runner dry harness that can execute exactly one command in a later lane, but keep execution disabled by default.
