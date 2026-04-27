# NotebookLM raw transcript hygiene status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-raw-transcript-hygiene`

## Goal

Prevent raw NotebookLM transcript artifacts from becoming committed provider evidence.

## Result

Added:

- `.gitignore` rules for raw/manual-gated NotebookLM artifacts
- `scripts/check_notebooklm_raw_transcripts.sh`
- `docs/contracts/notebooklm-raw-transcript-hygiene.md`
- `docs/progress/notebooklm-raw-transcript-hygiene-status.md`

Also removed previously committed dry-run raw transcript files where present. Redacted transcripts and redaction reports remain.

## Verification

Tests run:

```bash
bash -n scripts/check_notebooklm_raw_transcripts.sh
scripts/check_notebooklm_raw_transcripts.sh
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py polyglot-mini/tests/test_notebooklm_adapter.py polyglot-mini/tests/test_notebooklm_provider_output_wire.py polyglot-mini/tests/test_notebooklm_redaction.py polyglot-mini/tests/test_notebooklm_live_runner.py
git diff --check
```

## Next lane

Add this hygiene check to the broader verification path before any live NotebookLM probe.
