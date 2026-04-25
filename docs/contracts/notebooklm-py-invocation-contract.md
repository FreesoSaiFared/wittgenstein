# notebooklm-py invocation contract

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-contract`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-contract`

## Scope

This lane verifies the **local invocation contract** for `notebooklm-py`-style tooling only.
It does **not** implement real NotebookLM integration, browser automation, or external NotebookLM calls.

## Detected modules

Import probes were run for these module names:

- `notebooklm` -> `ModuleNotFoundError: No module named 'notebooklm'`
- `notebooklm_py` -> `ModuleNotFoundError: No module named 'notebooklm_py'`
- `notebooklm_py.client` -> `ModuleNotFoundError: No module named 'notebooklm_py'`
- `notebooklm.client` -> `ModuleNotFoundError: No module named 'notebooklm'`

Verdict: **no NotebookLM-related Python module is importable in this local environment**.

## Detected distributions

### Interpreter/tooling context

- `python` on `PATH` -> `ABSENT`
- `python3` on `PATH` -> `/home/linuxbrew/.linuxbrew/bin/python3`
- `python3 --version` -> `Python 3.14.3`
- `pip` on `PATH` -> `/usr/bin/pip`
- `pip --version` -> `pip 24.0 ... (python 3.12)`
- `python3 -m pip --version` -> `pip 26.0 ... (python 3.14)`

Because `pip` and `python3 -m pip` point at different interpreters, package detection was verified against the active `python3` interpreter as well as the shell `pip` command.

### Package queries

- `pip list | grep -i notebooklm` -> no matching rows
- `pip show notebooklm notebooklm-py notebooklm_py` -> `Package(s) not found`
- `python3 -m pip list | grep -i notebooklm` -> no matching rows
- `python3 -m pip show notebooklm notebooklm-py notebooklm_py` -> `Package(s) not found`
- `importlib.metadata.distributions()` filtered for `notebooklm` -> `NO_MATCHING_DISTRIBUTIONS`

Verdict: **no installed Python distribution matching `notebooklm` was detected**.

## Detected CLIs

- `command -v notebooklm` -> `ABSENT`
- `command -v notebooklm-py` -> `ABSENT`
- console-script scan across Python metadata for names containing `notebooklm` -> `NO_MATCHING_CONSOLE_SCRIPTS`

Because no executable exists on `PATH`, no `--help` or `--version` smoke probe was run.

## Safe commands tested

All tested commands were local-only:

- `command -v python`
- `command -v python3`
- `python3 --version`
- `command -v pip`
- `pip --version`
- `pip list | grep -i notebooklm`
- `pip show notebooklm notebooklm-py notebooklm_py`
- `python3 -m pip --version`
- `python3 -m pip list | grep -i notebooklm`
- `python3 -m pip show notebooklm notebooklm-py notebooklm_py`
- Python import probes for `notebooklm`, `notebooklm_py`, `notebooklm_py.client`, `notebooklm.client`
- Python `importlib.metadata` distribution scan for `notebooklm`
- `command -v notebooklm`
- `command -v notebooklm-py`
- Python entry-point scan for `console_scripts` names containing `notebooklm`

## External network calls

External NotebookLM calls were avoided.
All probes were limited to local process execution, import resolution, metadata inspection, or `PATH` lookup.

## Repo references inspected

Relevant local references found in this worktree:

- `polyglot-mini/polyglot/dossier.py` already contains `_detect_notebooklm_environment()`
- `polyglot-mini/tests/test_dossier.py` already checks structured `PROVIDER_UNAVAILABLE` behavior
- `docs/codecs/dossier.md` documents the provider seam
- `docs/progress/notebooklm-provider-status.md` records the earlier provider-lane absence result

## Exact verified invocation contract

**ABSENT**

There is **no verified local NotebookLM invocation path** in this environment.

Verified facts:

1. No importable NotebookLM-related module exists for the active `python3` interpreter.
2. No installed distribution containing `notebooklm` was found in Python metadata.
3. No `notebooklm` or `notebooklm-py` executable exists on `PATH`.
4. No console-script entry point matching `notebooklm` was found.

The only truthful contract today is the negative contract:

- local detection may safely inspect imports, distributions, entry points, and `PATH`
- if every probe is empty, the contract result is **ABSENT**
- no external NotebookLM call should be attempted from this environment

## Next implementation step

Install or vendor a **locally inspectable** NotebookLM package or CLI with a clearly safe smoke surface (for example `--help` or `--version`), then rerun this contract probe and update this document with:

1. exact executable and/or module name
2. exact command syntax
3. exact safe smoke command output
4. required environment variables, if any
5. whether import or CLI startup performs any network access

Until that exists, real NotebookLM integration should remain unimplemented and the current structured-unavailable provider seam should remain the truthful behavior.
