# NotebookLM adapter preflight status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-adapter-preflight`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-adapter-preflight`

## Goal

Add a minimal NotebookLM provider preflight and error taxonomy for the dossier seam without wiring a real adapter, browser automation, or real NotebookLM operations.

## Implemented

- Added `polyglot-mini/polyglot/notebooklm_provider.py` as a local-only NotebookLM provider seam.
- Added `preflight_notebooklm_provider()` that performs only local checks:
  - Python importability check for `notebooklm`
  - distribution scan for `notebooklm-py`
  - CLI presence check for `notebooklm`
  - optional configured storage/auth path check via `NOTEBOOKLM_HOME` or `NOTEBOOKLM_AUTH_JSON`
- Added structured preflight error taxonomy:
  - `NOTEBOOKLM_PACKAGE_MISSING`
  - `NOTEBOOKLM_CLI_MISSING`
  - `NOTEBOOKLM_STORAGE_MISSING`
  - `NOTEBOOKLM_AUTH_UNVERIFIED`
  - `NOTEBOOKLM_READY_UNVERIFIED`
- Wired dossier provider metadata to use the NotebookLM preflight.
- Preserved current dossier behavior:
  - `local` provider still succeeds
  - `notebooklm` still returns a structured failure until a real adapter exists
  - manifest and provider output now include richer preflight metadata and error codes

## Explicit non-goals preserved

This lane does **not**:

- run `notebooklm login`, `list`, `create`, `ask`, `source`, or `artifact`
- perform browser automation
- make network calls to NotebookLM
- wire a real NotebookLM adapter into dossier execution
- move NotebookLM into core codec logic

## Status model

- `unavailable`
  - required local package and/or CLI checks failed
- `not_ready`
  - local tooling is present, but auth readiness and real adapter execution remain unverified

`NOTEBOOKLM_READY_UNVERIFIED` remains intentional until a later lane implements and verifies a real adapter path.

## Verification

Primary regression suite:

```bash
PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py
```

Required smoke and diff checks are run in this lane before completion:

```bash
PYTHONPATH=polyglot-mini python3 -m polyglot.cli dossier "notebooklm preflight smoke" --provider notebooklm --sources polyglot-mini/polyglot/cli.py --out /tmp/notebooklm-preflight-smoke.md || true
git diff --check
```

## Next lane

A future adapter lane can build on this seam by:

1. choosing a real local invocation contract,
2. mapping typed auth/session/list failures to dossier errors,
3. verifying safe NotebookLM operations one surface at a time,
4. keeping NotebookLM as an optional provider rather than a core codec dependency.
