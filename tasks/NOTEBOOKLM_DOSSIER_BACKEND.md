# Task: Dossier / NotebookLM Context Backend

Implement a first-pass dossier codec/backend for Wittgenstein.

Use `.omx/prompts/CODEX_5_4_WITTGENSTEIN_NOTEBOOKLM_MISSION.md` as the controlling mission prompt.

Acceptance criteria:
- Local provider works without network.
- NotebookLM provider is a clear seam, real if safe, structured error if not.
- Every run writes manifest + source ledger + claim ledger + context pack + markdown context.
- Offline replay works.
- Context pack is pointer-heavy and claim-addressable.
- Tests/smoke checks run.
