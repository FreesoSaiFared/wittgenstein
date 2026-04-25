# NotebookLM install probe status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-install-probe`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-install-probe`

## Goal completed

Produce a reproducible local install/probe artifact for `notebooklm-py` without integrating real NotebookLM yet.

## Scope completed

- Added a reproducible helper: `scripts/notebooklm_py_install_probe.sh`
- Installed `notebooklm-py` in an isolated temporary venv under `/tmp`
- Captured exact package, import, distribution, entry-point, and CLI-help metadata
- Wrote the dedicated install probe contract doc
- Updated the invocation contract doc to reflect the verified isolated-venv contract
- Left dossier-core untouched
- Avoided browser automation and real NotebookLM operations

## Verified result

The install probe succeeded in `/tmp/witt-notebooklm-py-probe-venv`.

Verified local mapping:

- distribution: `notebooklm-py 0.3.4`
- import package: `notebooklm`
- working client import: `notebooklm.client`
- CLI executable: `notebooklm`
- missing executable alias: `notebooklm-py`
- safe smoke command: `notebooklm --help`

## Decision

NotebookLM remains **unintegrated** in Wittgenstein, but there is now a verified local install/probe artifact showing how the third-party package presents itself when installed in isolation.

This means future adapter work should target the contract below rather than guessing names from the PyPI distribution:

- install `notebooklm-py`
- import `notebooklm`
- invoke `notebooklm`

## Explicit non-goals preserved

- no real NotebookLM adapter
- no auth flow
- no browser automation
- no dossier-core rewrite
- no committed virtualenv

## Next step

If a later lane decides to prototype a real adapter, start from `docs/contracts/notebooklm-py-invocation-contract.md`, keep the current `--help` smoke surface as the first guardrail, and verify network/auth behavior separately before touching dossier-core.
