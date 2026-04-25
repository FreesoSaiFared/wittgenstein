# NotebookLM auth preflight status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-auth-preflight`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-auth-preflight`

## Goal completed

Document NotebookLM auth/session failure semantics for the installed `notebooklm-py` CLI/API surface without performing any mutating NotebookLM actions.

## Scope completed

- Verified the existing isolated probe venv still works and `notebooklm --help` succeeds.
- Recreated a hermetic temp home at `/tmp/witt-notebooklm-auth-preflight-home`.
- Ran only read-only/status/help probes plus a Python `NotebookLMClient.from_storage()` missing-storage probe.
- Captured exit codes and sanitized stdout/stderr.
- Wrote the auth/session preflight contract doc.
- Left dossier-core untouched.
- Avoided browser automation and all notebook create/delete/ask/source/artifact operations.

## Verified auth/session semantics

- `notebooklm status` exits `0` and reports `No notebook selected...` even in an empty unauthenticated temp home.
- `notebooklm auth check` exits `0` while rendering multiple failed auth checks and a `Storage file not found` error.
- `notebooklm list` is a read-only listing command per help text and exits `1` with `Not logged in.` when auth storage is absent.
- `NotebookLMClient.from_storage()` raises `FileNotFoundError` for missing storage and includes a login hint in the exception message.

## Decision

Future adapter work should treat NotebookLM auth preflight as a **structured failure classification problem**, not as a simple CLI exit-code check.

Most important consequences:

1. `status` cannot serve as the auth gate.
2. `auth check` diagnostics must be interpreted by content, not exit code alone.
3. `from_storage()` currently provides the cleanest typed missing-storage failure.
4. Missing auth storage, unauthenticated access, and missing notebook context should remain separate error classes.

## Deliverables

- `docs/contracts/notebooklm-auth-preflight.md`
- `docs/progress/notebooklm-auth-preflight-status.md`
