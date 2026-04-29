# Wittgenstein Agent Protocol

## Role & Intent

You are developing Wittgenstein as an LLM-to-world compiler: prompt -> typed IR -> renderer/tool/action -> artifact -> manifest. Do not treat this as a normal chat integration. Every external system must be wrapped behind a codec/backend boundary with schemas, traces, and replay artifacts.

## Hard Rules

1. Preserve Wittgenstein's five-layer model:
   - L1 runtime/harness
   - L2 IR/codec schemas
   - L3 renderer/decoder/provider operation
   - L4 optional adapter/provider bridge
   - L5 CLI/docs/distribution/agent primers
2. No silent fallbacks. If provider route changes, record the decision in the manifest.
3. Start experimental work in `polyglot-mini/` unless the task explicitly requires TypeScript harness changes.
4. Every new operation must produce or update an artifact under `artifacts/runs/<run-id>/` or an equivalent deterministic test fixture.
5. NotebookLM is volatile. Capture raw output, normalize it, hash it, and support offline replay from captured artifacts.
6. Codex patches must be linked to claim IDs from the context pack. No anonymous implementation prose.
7. Do not use raw NotebookLM summaries as implementation facts. Extract claims, verify against local sources where possible, and quarantine unverified claims.
8. Run verification before claiming completion:
   - `pnpm typecheck`
   - targeted tests
   - relevant CLI smoke command
   - manifest/artifact inspection
9. Keep changes small per worktree lane. If a task crosses more than two packages, create or update a plan first.
10. Prefer JSON/NDJSON machine-readable surfaces where possible.

## Development Lanes

- `dossier-core`: polyglot dossier codec, claim ledger, offline replay
- `notebooklm-provider`: notebooklm-py provider adapter and volatile capture
- `codex-handoff`: codex context pack, patch ledger, parent/child run linkage
- `omx-integration`: oh-my-codex hooks/adapt/tool surface and project instructions
- `qa-docs`: tests, fixtures, docs, smoke scripts

## Completion Standard

A task is complete only when:
- implementation is committed in the lane branch,
- tests or smoke checks were run and recorded,
- docs or examples were updated when user-facing behavior changed,
- generated artifacts can be traced to inputs,
- any remaining uncertainty is written into a follow-up file, not hidden in chat.
