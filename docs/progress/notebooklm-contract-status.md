# NotebookLM contract lane status

Date: 2026-04-25
Branch: `feat/nblm/notebooklm-contract`
Worktree: `/home/ned/src/ai-work/wittgenstein-worktrees/notebooklm-contract`

## Goal

Discover and document the exact local invocation contract for `notebooklm-py`, or prove that the contract is absent/unclear, without implementing real NotebookLM integration.

## Commands run

### Python environment

```bash
command -v python || true
command -v python3 || true
python3 --version
command -v pip || true
pip --version
pip list | grep -i notebooklm || true
pip show notebooklm notebooklm-py notebooklm_py || true
python3 -m pip --version
python3 -m pip list | grep -i notebooklm || true
python3 -m pip show notebooklm notebooklm-py notebooklm_py || true
python3 - <<'PY'
import importlib
mods = ['notebooklm', 'notebooklm_py', 'notebooklm_py.client', 'notebooklm.client']
for name in mods:
    try:
        mod = importlib.import_module(name)
        print(f'IMPORT_OK\t{name}\t{getattr(mod, "__file__", None)}')
    except Exception as e:
        print(f'IMPORT_FAIL\t{name}\t{type(e).__name__}: {e}')
PY
python3 - <<'PY'
import importlib.metadata as md
found = False
for dist in md.distributions():
    name = dist.metadata.get('Name') or ''
    summary = dist.metadata.get('Summary') or ''
    if 'notebooklm' in name.lower() or 'notebooklm' in summary.lower():
        found = True
        print(f'{name}\t{dist.version}')
if not found:
    print('NO_MATCHING_DISTRIBUTIONS')
PY
```

### CLI availability

```bash
command -v notebooklm || true
command -v notebooklm-py || true
python3 - <<'PY'
import importlib.metadata as md
found = False
for dist in md.distributions():
    for ep in dist.entry_points:
        if ep.group == 'console_scripts' and 'notebooklm' in ep.name.lower():
            found = True
            print(f'{dist.metadata.get("Name")}\t{dist.version}\t{ep.name}\t{ep.value}')
if not found:
    print('NO_MATCHING_CONSOLE_SCRIPTS')
PY
```

No NotebookLM executable existed on `PATH`, so no `--help` or `--version` smoke command was run.

### Repo references

```bash
rg -n --hidden --glob '!.git' --glob '!.venv' --glob '!node_modules' \
  'notebooklm|notebooklm-py|provider=notebooklm|PROVIDER_UNAVAILABLE' . || true
```

## Results

### Python/package detection

- `python`: absent on `PATH`
- `python3`: `/home/linuxbrew/.linuxbrew/bin/python3`
- `python3 --version`: `Python 3.14.3`
- `pip`: `/usr/bin/pip` (`python 3.12`)
- `python3 -m pip --version`: `pip 26.0` for `python 3.14`
- neither `pip` nor `python3 -m pip` reported a NotebookLM-related package
- all requested import probes failed with `ModuleNotFoundError`
- `importlib.metadata` returned `NO_MATCHING_DISTRIBUTIONS`

### CLI detection

- `notebooklm` executable: absent
- `notebooklm-py` executable: absent
- matching `console_scripts`: none found
- no executable existed, so no `--help` or `--version` command was run

### Repo references

Notable local references:

- `polyglot-mini/polyglot/dossier.py` contains `_detect_notebooklm_environment()`
- `polyglot-mini/tests/test_dossier.py` asserts structured `PROVIDER_UNAVAILABLE`
- `docs/codecs/dossier.md` documents the provider seam
- `docs/progress/notebooklm-provider-status.md` already records the earlier provider-lane absence result

## Decision

`docs/contracts/notebooklm-py-invocation-contract.md` records an explicit **ABSENT** verdict for the local NotebookLM invocation contract in this environment.

## Notes

- External network calls were intentionally avoided.
- No browser automation was added.
- `dossier-core` was not rewritten.
- No helper script was added because the repo already contains a local-only detection seam in `polyglot-mini/polyglot/dossier.py` and the new docs fully capture the verified contract state.
