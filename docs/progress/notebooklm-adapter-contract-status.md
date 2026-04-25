# NotebookLM adapter contract status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-adapter-contract`

## Goal

Define the smallest real NotebookLM adapter boundary before implementation.

## Result

Added a contract-only boundary for future NotebookLM adapter work.

Deliverables:

- `docs/contracts/notebooklm-adapter-contract.md`
- `docs/schemas/notebooklm-provider-result-v0.json`
- `docs/progress/notebooklm-adapter-contract-status.md`

## Contract summary

The contract defines:

- ProviderRequest shape.
- ProviderResult shape.
- provider-output.md capture rules.
- manifest metadata rules.
- provider error taxonomy.
- claim promotion boundaries.
- replay constraints.
- adapter implementation implications.

The central rule is:

```text
NotebookLM can inform; local artifacts decide.
```

## Verification

No real NotebookLM operation was performed.
No browser automation was added.
No adapter was wired.

Tests run:

```bash
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py
python3 -m json.tool docs/schemas/notebooklm-provider-result-v0.json >/dev/null
git diff --check
```

## Next lane

Add a pure local adapter skeleton matching this contract. It should return structured not-ready results and must not call NotebookLM.
