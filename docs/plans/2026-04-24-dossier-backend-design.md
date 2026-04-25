# Dossier Backend Design

## Summary
Implement a deterministic dossier backend in the Python prototype surface. The local provider scans bounded repository sources, records a source ledger, extracts claim-addressable evidence, builds a pointer-heavy Codex context pack, and renders a markdown handoff document. NotebookLM is modeled as a provider seam that must either run safely or fail with a structured error.

## Chosen approach
- Add a new `dossier` route to `polyglot-mini/polyglot/cli.py`.
- Add a root-level `polyglot` namespace shim so `python3 -m polyglot.cli` works from repo root.
- Keep the backend deterministic: local provider only, stable file ordering, stable scoring, stable claim IDs.
- Emit canonical dossier artifacts under `artifacts/runs/<run-id>/`, then copy the rendered context markdown to `--out`.
- Add a `dossier-replay` CLI route that rebuilds markdown from `claim-ledger.json`, `source-ledger.json`, and `codex-context-pack.json`.

## Trade-offs considered
1. **All-in-one single file backend** — fastest, but would become noisy and hard to test. Rejected.
2. **Multi-module dossier package inside `polyglot-mini/polyglot/`** — chosen; keeps provider, extraction, and replay logic testable.
3. **Immediate TypeScript monorepo implementation** — rejected for first pass because the mission explicitly prefers `polyglot-mini/` and the work is still experimental.

## Testing shape
- Red/green Python tests first for claim extraction, source-ledger creation, context pack shape, structured notebooklm failure, replay, and CLI import/route behavior.
- Manual smoke run against the repo itself to inspect artifacts.

## Mechanical authority boundary
Add two rendered contexts: `planner-context.md` and `executor-context.md`. Only implementation-authorized claims and promoted decisions flow into executor context. Add `patch-ledger.json` and a deterministic `verify-patch-authority` path that rejects hunks tied to planning-only or stale claims.
