# NotebookLM CLI surface status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-cli-surface`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-cli-surface`

## Goal completed

Document the local CLI and Python API surface exposed by the installed `notebooklm-py` package without performing real NotebookLM operations.

## Commands run

### Probe environment

```bash
if [ ! -x /tmp/witt-notebooklm-py-probe-venv/bin/python ]; then
  ./scripts/notebooklm_py_install_probe.sh
fi
source /tmp/witt-notebooklm-py-probe-venv/bin/activate
command -v python
command -v notebooklm
notebooklm --help
```

### Top-level CLI help capture

```bash
for cmd in \
  login use status clear list create delete rename summary ask configure history \
  source artifact note share research generate download auth language metadata skill
  do
    notebooklm "$cmd" --help
  done
```

### Python/package introspection

```bash
python - <<'PY'
import importlib
import importlib.metadata as md
import inspect

import notebooklm
import notebooklm.client
import notebooklm.notebooklm_cli
PY
```

```bash
python - <<'PY'
from notebooklm.notebooklm_cli import cli
import click

def walk(cmd, prefix='notebooklm'):
    print(prefix)
    if isinstance(cmd, click.core.Group):
        for name, sub in cmd.commands.items():
            walk(sub, f'{prefix} {name}')

walk(cli)
PY
```

### Installed source inspection

```bash
sed -n '1,220p' /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/__init__.py
sed -n '1,260p' /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/client.py
sed -n '1,260p' /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/notebooklm_cli.py
sed -n '1,220p' /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/auth.py
sed -n '1,220p' /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/paths.py
find /tmp/witt-notebooklm-py-probe-venv/lib/python3.14/site-packages/notebooklm/cli -maxdepth 1 -type f | sort
```

## Findings

### Verified package identity

- distribution: `notebooklm-py 0.3.4`
- import package: `notebooklm`
- client module: `notebooklm.client`
- console script: `notebooklm -> notebooklm.notebooklm_cli:main`
- probe executable path: `/tmp/witt-notebooklm-py-probe-venv/bin/notebooklm`

### Verified safe CLI behavior

- `notebooklm --help` works inside the probe venv
- all inspected top-level subcommands accepted `--help`
- command groups expose a large nested tree for sources, artifacts, notes, sharing, research, generation, downloads, language, auth, and skill integration

### Verified Python API shape

- `notebooklm.__init__` exports a broad public API centered on `NotebookLMClient`
- `NotebookLMClient` is async-oriented and builds namespaced APIs for notebooks, sources, notes, artifacts, chat, research, settings, and sharing
- installed source code makes the package's real-runtime dependency on auth/session handling explicit

### Verified auth/path implications

- default NotebookLM home path: `~/.notebooklm`
- environment override: `NOTEBOOKLM_HOME`
- default storage file: `~/.notebooklm/storage_state.json`
- auth source code fetches fresh tokens from `https://notebooklm.google.com/`, so real client usage is not a local-only action

### Important limits preserved

- no login flow was executed
- no notebook list/create/delete/ask/chat/source/artifact/generate/download operation was executed
- no browser automation was added
- dossier-core was not modified

## Extra note from introspection

A direct `inspect.signature()` pass over some installed async methods hit a Python 3.14 annotation-evaluation `TypeError` inside the package. Source reading and lighter member inspection were used instead. This did not block surface mapping, but it is a useful compatibility note.

## Deliverables

- `docs/contracts/notebooklm-cli-surface.md`
- `docs/progress/notebooklm-cli-surface-status.md`
