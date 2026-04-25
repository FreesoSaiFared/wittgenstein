# notebooklm-py install probe

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-install-probe`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-install-probe`

## Goal

Create a **locally reproducible install/probe artifact** for `notebooklm-py` without wiring real NotebookLM into Wittgenstein yet.

This probe is intentionally narrow:

- create an isolated venv under `/tmp`
- install `notebooklm-py`
- capture package/import/CLI metadata only
- avoid browser automation and real NotebookLM calls
- leave dossier-core unchanged

## Reproduction

The lane now includes a helper:

```bash
./scripts/notebooklm_py_install_probe.sh
```

Default outputs:

- venv: `/tmp/witt-notebooklm-py-probe-venv`
- raw report: `/tmp/witt-notebooklm-py-probe-report.txt`
- pip upgrade log: `/tmp/witt-notebooklm-py-upgrade-pip.log`

The helper deletes and recreates the probe venv each run so the result is deterministic at the package-resolution level for that moment in time.

## Exact verified install result

Probe run date: 2026-04-25

- venv creation: `python3 -m venv /tmp/witt-notebooklm-py-probe-venv`
- interpreter inside probe venv: `Python 3.14.3`
- pip inside probe venv: `pip 26.0.1`
- install command: `python -m pip install notebooklm-py`
- install result: `SUCCESS`
- resolved distribution: `notebooklm-py 0.3.4`
- package summary: `Unofficial Python library for automating Google NotebookLM`
- package home page: `https://github.com/teng-lin/notebooklm-py`

## Exact metadata captured

### `pip show`

- `python -m pip show notebooklm-py` -> found `notebooklm-py 0.3.4`
- `python -m pip show notebooklm` -> `WARNING: Package(s) not found: notebooklm`
- `python -m pip show notebooklm_py` -> found `notebooklm-py 0.3.4`

The underscore/hyphen alias is normalized by pip metadata lookup, but the installed distribution name is still `notebooklm-py`.

### Import probes

- `import notebooklm` -> **OK** (`.../site-packages/notebooklm/__init__.py`)
- `import notebooklm_py` -> **FAIL** (`ModuleNotFoundError`)
- `import notebooklm_py.client` -> **FAIL** (`ModuleNotFoundError`)
- `import notebooklm.client` -> **OK** (`.../site-packages/notebooklm/client.py`)

### `importlib.metadata` distributions containing `notebooklm`

- `notebooklm-py    0.3.4    Unofficial Python library for automating Google NotebookLM`

### Console scripts containing `notebooklm`

- `notebooklm-py    0.3.4    notebooklm    notebooklm.notebooklm_cli:main`

### Commands found inside the probe venv

- `command -v notebooklm` -> `/tmp/witt-notebooklm-py-probe-venv/bin/notebooklm`
- `command -v notebooklm-py` -> absent

### CLI smoke probe

Verified safe smoke command:

```bash
source /tmp/witt-notebooklm-py-probe-venv/bin/activate
notebooklm --help
```

Verified result: the CLI prints help text locally and exits successfully. The help surface advertises subcommands such as `login`, `list`, `create`, `ask`, `source`, `artifact`, and `research`, but those operational commands were **not** executed in this lane.

## Verified local contract

Inside the isolated probe venv, the verified local contract is:

1. **Install name:** `notebooklm-py`
2. **Primary import package:** `notebooklm`
3. **Working client import:** `notebooklm.client`
4. **Primary console command:** `notebooklm`
5. **Verified safe smoke surface:** `notebooklm --help`

Negative facts that are equally important:

1. `notebooklm_py` is **not** the working import package.
2. `notebooklm-py` is **not** the installed executable name.
3. No real NotebookLM session/auth/list/create/chat call has been verified.
4. This package describes itself as **unofficial**.

## Boundaries kept

This lane did **not**:

- rewrite `dossier-core`
- add browser automation
- wire a real NotebookLM adapter
- run NotebookLM auth or notebook operations
- claim that repo-global `PATH` now includes `notebooklm`

The verified contract exists only inside the temporary probe venv unless another installation step is added later.

## Raw artifact

The exact probe transcript is written locally to:

```text
/tmp/witt-notebooklm-py-probe-report.txt
```

That file is intentionally not committed.
