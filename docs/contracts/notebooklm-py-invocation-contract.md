# notebooklm-py invocation contract

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-install-probe`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-install-probe`

## Scope

This lane verifies the **isolated local invocation contract** for `notebooklm-py` only.
It does **not** implement real NotebookLM integration, browser automation, or external NotebookLM calls.

## Verified setup

The verified probe setup is:

```bash
python3 -m venv /tmp/witt-notebooklm-py-probe-venv
source /tmp/witt-notebooklm-py-probe-venv/bin/activate
python -m pip install notebooklm-py
```

Verified interpreter inside the probe venv:

- `python --version` -> `Python 3.14.3`
- `python -m pip --version` -> `pip 26.0.1`

Verified installed distribution:

- `python -m pip show notebooklm-py` -> `notebooklm-py 0.3.4`
- `python -m pip show notebooklm` -> not found
- `python -m pip show notebooklm_py` -> resolves to `notebooklm-py 0.3.4`

## Detected modules

Import probes were run for these module names:

- `notebooklm` -> import **OK**
- `notebooklm_py` -> `ModuleNotFoundError: No module named 'notebooklm_py'`
- `notebooklm_py.client` -> `ModuleNotFoundError: No module named 'notebooklm_py'`
- `notebooklm.client` -> import **OK**

Verdict: the working Python import surface is **`notebooklm`**, not `notebooklm_py`.

## Detected distributions

`importlib.metadata.distributions()` filtered for `notebooklm` returned:

- `notebooklm-py    0.3.4    Unofficial Python library for automating Google NotebookLM`

Verdict: the verified install name is **`notebooklm-py`**.

## Detected CLIs

- `command -v notebooklm` -> `/tmp/witt-notebooklm-py-probe-venv/bin/notebooklm`
- `command -v notebooklm-py` -> `ABSENT`
- console-script scan across Python metadata for names containing `notebooklm` ->
  - `notebooklm-py    0.3.4    notebooklm    notebooklm.notebooklm_cli:main`

Verified smoke command:

```bash
source /tmp/witt-notebooklm-py-probe-venv/bin/activate
notebooklm --help
```

Verdict: the working CLI surface is **`notebooklm`**, not `notebooklm-py`.

## Safe commands tested

All tested commands were constrained to the isolated probe venv and local metadata inspection:

- `python3 -m venv /tmp/witt-notebooklm-py-probe-venv`
- `source /tmp/witt-notebooklm-py-probe-venv/bin/activate`
- `python -m pip install notebooklm-py`
- `python --version`
- `python -m pip --version`
- `python -m pip show notebooklm-py notebooklm notebooklm_py`
- Python import probes for `notebooklm`, `notebooklm_py`, `notebooklm_py.client`, `notebooklm.client`
- Python `importlib.metadata` distribution scan for `notebooklm`
- Python entry-point scan for `console_scripts` names containing `notebooklm`
- `command -v notebooklm`
- `command -v notebooklm-py`
- `notebooklm --help`

## External network calls

The only network use in this lane was package installation into the temporary venv:

- `python -m pip install notebooklm-py`

No real NotebookLM API/browser/auth/list/create/chat operation was executed.

## Exact verified invocation contract

**POSITIVE, BUT ONLY INSIDE THE ISOLATED PROBE VENV**

Verified facts:

1. Install the distribution as `notebooklm-py`.
2. Import the library as `notebooklm`.
3. Import the client module as `notebooklm.client`.
4. Invoke the CLI as `notebooklm`.
5. Use `notebooklm --help` as the currently verified safe smoke command.

The truthful contract today is:

- a local probe may recreate the temp venv and install `notebooklm-py`
- code should not assume `notebooklm_py` is the import name
- code should not assume `notebooklm-py` is the executable name
- real NotebookLM operations remain unverified and out of scope

## Non-contract / still unverified

These behaviors were **not** verified and must not be assumed:

- `notebooklm login`
- `notebooklm list`
- notebook creation/deletion/chat/artifact commands
- browser automation requirements
- auth/session persistence behavior
- whether runtime imports or non-help CLI commands trigger network activity
- whether the unofficial package is stable enough for Wittgenstein integration

## Next implementation step

If a later lane explores a real adapter, begin from this exact mapping:

- PyPI install target: `notebooklm-py`
- Python import target: `notebooklm`
- CLI target: `notebooklm`

Then separately verify auth, network, artifact capture, and failure semantics before touching dossier-core.
