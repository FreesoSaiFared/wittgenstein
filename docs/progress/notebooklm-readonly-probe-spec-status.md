# NotebookLM read-only probe spec status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-readonly-probe-spec`

## Goal

Name exactly one future read-only NotebookLM probe operation while still not executing it.

## Result

Added:

- `docs/contracts/notebooklm-readonly-probe-spec.md`
- `docs/schemas/notebooklm-readonly-probe-spec-v0.json`
- `scripts/notebooklm_readonly_probe_spec.sh`
- `docs/progress/notebooklm-readonly-probe-spec-status.md`
- dry-run artifacts under `artifacts/manual-gated/notebooklm/readonly-probe-spec-dry-run/`

## Named future operation

```text
readonly-list -> notebooklm list
```

This is not approved for execution in this lane.

## Verification

Tests run:

```bash
bash -n scripts/notebooklm_readonly_probe_spec.sh
./scripts/notebooklm_readonly_probe_spec.sh
python3 -m json.tool docs/schemas/notebooklm-readonly-probe-spec-v0.json >/dev/null
python3 -m json.tool artifacts/manual-gated/notebooklm/readonly-probe-spec-dry-run/request.json >/dev/null
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py
git diff --check
```

## Next lane

Add a gated runner mode for `readonly-list` that still defaults to policy-blocked unless a future explicit enable variable is present.
