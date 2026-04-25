# NotebookLM provider status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-provider`

## Scope completed

- Kept dossier local-first.
- Added an explicit `notebooklm` provider seam to the dossier CLI.
- Preserved the existing local provider behavior.
- Preserved offline replay by continuing to write the normal dossier artifact spine even when the NotebookLM provider is unavailable.
- Returned a structured `PROVIDER_UNAVAILABLE` result instead of crashing when NotebookLM cannot be safely used.

## notebooklm-py detection

Environment checks were limited to local inspection only.

- Python module `notebooklm`: not found
- Python module `notebooklm_py`: not found
- Installed distributions containing `notebooklm`: none found
- CLI candidates `notebooklm` / `notebooklm-py`: none found on `PATH`
- Safe smoke command: none detected

Result: dossier records NotebookLM as `unavailable` in this environment.

## Current behavior

Running `polyglot dossier ... --provider notebooklm` now:

- recognizes the provider name
- writes `source-ledger.json`
- writes `claim-ledger.json`
- writes `codex-context-pack.json`
- writes `planner-context.md`
- writes `executor-context.md`
- writes `provider-output.md`
- writes `manifest.json`
- returns a structured `PROVIDER_UNAVAILABLE` result with captured provider metadata

Replay remains offline because it re-renders from the saved artifacts and does not probe NotebookLM again.

## Exact next step for real NotebookLM integration

Install and document a verified local `notebooklm-py` package/CLI that supports a **non-network safe smoke command** (for example a local `--help` or version probe), then replace the current structured-unavailable branch with a thin adapter that:

1. records the verified invocation contract in docs
2. captures provider request/response metadata in `provider-output.md`
3. keeps all authority production local/deterministic unless a later decision explicitly broadens the boundary
