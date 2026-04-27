# notebooklm auth/session preflight

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-auth-preflight`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-auth-preflight`
Probe venv: `/tmp/witt-notebooklm-py-probe-venv`
Hermetic temp home: `/tmp/witt-notebooklm-auth-preflight-home`
Package: `notebooklm-py 0.3.4`

## Goal

Document **auth/session failure semantics** for the installed `notebooklm-py` CLI/API surface without creating or deleting notebooks, asking NotebookLM questions, adding browser automation, or wiring a real Wittgenstein adapter.

## Temp-home setup

The probe used a reset temporary home:

```bash
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-auth-preflight-home
export HOME="$NOTEBOOKLM_HOME"
rm -rf "$NOTEBOOKLM_HOME"
mkdir -p "$NOTEBOOKLM_HOME"
```

Why both variables were set:

- `NOTEBOOKLM_HOME` is what the CLI reports in its auth-related diagnostics.
- `HOME` also had to match the temp home so the CLI's computed default `--storage` path became hermetic.
- Evidence: under this setup, `notebooklm --help` reported the default storage path as `/tmp/witt-notebooklm-auth-preflight-home/storage_state.json`.

## Commands run

```bash
if [ ! -x /tmp/witt-notebooklm-py-probe-venv/bin/notebooklm ]; then
  ./scripts/notebooklm_py_install_probe.sh
fi

source /tmp/witt-notebooklm-py-probe-venv/bin/activate
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-auth-preflight-home
export HOME="$NOTEBOOKLM_HOME"
rm -rf "$NOTEBOOKLM_HOME"
mkdir -p "$NOTEBOOKLM_HOME"

notebooklm --help
notebooklm status || true
notebooklm auth check || true
notebooklm list || true

python - <<'PY'
import asyncio
import os
from notebooklm import NotebookLMClient

path = os.path.join(os.environ['NOTEBOOKLM_HOME'], 'missing-storage', 'storage_state.json')

async def main():
    try:
        await NotebookLMClient.from_storage(path)
    except Exception as e:
        print(type(e).__name__)
        print(str(e))

asyncio.run(main())
PY
```

`notebooklm list` was included because `notebooklm --help` explicitly described it as `List all notebooks.`, which is a read-only listing surface.

A sanitization pass was applied to captured stdout/stderr for token/cookie-like strings. No secret values were present in the observed outputs, so no redactions were needed.

## Exit codes and sanitized outputs

### `notebooklm --help`

- Exit code: `0`

```text
Usage: notebooklm [OPTIONS] COMMAND [ARGS]...

  NotebookLM CLI.

  Quick start:
    notebooklm login              # Authenticate first
    notebooklm list               # List your notebooks
    notebooklm create "My Notes"  # Create a notebook
    notebooklm ask "Hi"           # Ask the current notebook a question

Options:
  --version       Show the version and exit.
  --storage PATH  Path to storage_state.json (default: /tmp/witt-notebooklm-
                  auth-preflight-home/storage_state.json)
  -v, --verbose   Increase verbosity (-v for INFO, -vv for DEBUG)
  --help          Show this message and exit.

Session:
  login   Log in to NotebookLM via browser.
  use     Set the current notebook context.
  status  Show current context (active notebook and conversation).
  clear   Clear current notebook context.

Notebooks:
  list     List all notebooks.
  create   Create a new notebook.
  delete   Delete a notebook.
  rename   Rename a notebook.
  summary  Get notebook summary with AI-generated insights.
```

### `notebooklm status`

- Exit code: `0`

```text
No notebook selected. Use 'notebooklm use <id>' to set one.
```

### `notebooklm auth check`

- Exit code: `0`

```text
                              Authentication Check
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check           ┃ Status    ┃ Details                                        ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Storage exists  │ ✗ fail    │ $NOTEBOOKLM_HOME                               │
│                 │           │ (/tmp/witt-notebooklm-auth-preflight-home/sto… │
│ JSON valid      │ ✗ fail    │                                                │
│ Cookies present │ ✗ fail    │                                                │
│ SID cookie      │ ✗ fail    │                                                │
│ Token fetch     │ ⊘ skipped │ use --test to check                            │
└─────────────────┴───────────┴────────────────────────────────────────────────┘

Error: Storage file not found:
/tmp/witt-notebooklm-auth-preflight-home/storage_state.json

Run 'notebooklm login' to authenticate.
```

### `notebooklm list`

- Exit code: `1`

```text
Not logged in.

Checked locations:
  • Storage file: /tmp/witt-notebooklm-auth-preflight-home/storage_state.json
    (via $NOTEBOOKLM_HOME)
  • NOTEBOOKLM_AUTH_JSON: not set

Options to authenticate:
  1. Run: notebooklm login
  2. Set NOTEBOOKLM_AUTH_JSON env var (for CI/CD)
  3. Use --storage /path/to/file.json flag
```

### Python API probe: `NotebookLMClient.from_storage()` against missing storage

- Exit code of the probe wrapper: `0`
- Underlying API result: raised `FileNotFoundError`

```text
FileNotFoundError
Storage file not found: /tmp/witt-notebooklm-auth-preflight-home/missing-storage/storage_state.json
Run 'notebooklm login' to authenticate first.
```

Observed traceback root from the installed package:

- `notebooklm/client.py:141` -> `await AuthTokens.from_storage(storage_path)`
- `notebooklm/auth.py:195` -> `load_auth_from_storage(path)`
- `notebooklm/auth.py:431` -> `raise FileNotFoundError(...)`

## Observed failure classes and messages

### 1. Missing auth storage file

Observed in both CLI and Python API paths.

- CLI message shape: `Storage file not found: .../storage_state.json`
- Python exception type: `FileNotFoundError`
- Recovery hint included by package: `Run 'notebooklm login' to authenticate first.`

### 2. Unauthenticated listing request

Observed in `notebooklm list`.

- Exit code: `1`
- Primary message: `Not logged in.`
- Extra diagnostics enumerate candidate auth locations and remediation options.

### 3. No active notebook context

Observed in `notebooklm status`.

- Exit code: `0`
- Message: `No notebook selected. Use 'notebooklm use <id>' to set one.`
- Important nuance: in an empty unauthenticated temp home, `status` reports missing notebook context rather than missing auth.

### 4. Diagnostic auth check that still exits successfully

Observed in `notebooklm auth check`.

- Exit code: `0`
- Output contains multiple explicit failures (`Storage exists`, `JSON valid`, `Cookies present`, `SID cookie`) plus an `Error:` block.
- This means failure is encoded in the rendered table/message, not in the process exit status.

## Implications for structured provider errors

These observations are enough to shape a future adapter error contract without wiring one yet.

### Recommended distinctions

1. **Auth storage missing / unreadable**
   - Trigger source: `FileNotFoundError` from `NotebookLMClient.from_storage()` or CLI output containing `Storage file not found:`
   - Should map to a structured provider error distinct from generic unavailability.

2. **Auth required / not logged in**
   - Trigger source: `notebooklm list` exit `1` with `Not logged in.`
   - Should preserve `checked_locations`-style diagnostics in error details when available.

3. **Notebook context missing**
   - Trigger source: `notebooklm status` exit `0` with `No notebook selected.`
   - Must not be conflated with auth success.

4. **Diagnostic failure with zero exit code**
   - Trigger source: `notebooklm auth check`
   - Adapter logic cannot trust exit code alone; it must inspect structured API exceptions or CLI output content.

### Concrete adapter design implications

- `status` is **not** a reliable auth preflight gate.
- `auth check` is useful for diagnostics, but a zero exit code does **not** imply success.
- `NotebookLMClient.from_storage()` gives the cleanest typed failure for missing storage (`FileNotFoundError`).
- A future NotebookLM provider should prefer **typed API exceptions** when possible and use CLI output parsing only as a fallback.
- For Wittgenstein's dossier/provider seam, these failures should become structured error codes/details rather than collapsing into a generic crash or a generic `PROVIDER_UNAVAILABLE` message.

## Boundaries preserved

This lane did **not**:

- create or delete notebooks
- ask NotebookLM questions
- add sources or generate artifacts
- add browser automation
- wire a real adapter
- rewrite dossier-core
