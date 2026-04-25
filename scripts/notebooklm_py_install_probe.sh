#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PATH="${VENV_PATH:-/tmp/witt-notebooklm-py-probe-venv}"
REPORT_PATH="${REPORT_PATH:-/tmp/witt-notebooklm-py-probe-report.txt}"
PIP_UPGRADE_LOG="${PIP_UPGRADE_LOG:-/tmp/witt-notebooklm-py-upgrade-pip.log}"

rm -rf "$VENV_PATH"
"$PYTHON_BIN" -m venv "$VENV_PATH"
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip >"$PIP_UPGRADE_LOG" 2>&1

{
  echo '## INSTALL'
  echo "venv=$VENV_PATH"
  python --version
  python -m pip --version
  echo '$ python -m pip install notebooklm-py'
  python -m pip install notebooklm-py
  echo
  echo '## PYTHON_VERSION'
  python --version
  echo
  echo '## PIP_SHOW'
  python -m pip show notebooklm-py || true
  echo '---'
  python -m pip show notebooklm || true
  echo '---'
  python -m pip show notebooklm_py || true
  echo
  echo '## IMPORT_PROBES'
  python - <<'PY'
import importlib
mods = ['notebooklm', 'notebooklm_py', 'notebooklm_py.client', 'notebooklm.client']
for name in mods:
    try:
        mod = importlib.import_module(name)
        print(f'IMPORT_OK\t{name}\t{getattr(mod, "__file__", None)}')
    except Exception as e:
        print(f'IMPORT_FAIL\t{name}\t{type(e).__name__}: {e}')
PY
  echo
  echo '## DISTRIBUTIONS_CONTAINING_NOTEBOOKLM'
  python - <<'PY'
import importlib.metadata as md
matches = []
for dist in md.distributions():
    name = dist.metadata.get('Name') or ''
    summary = dist.metadata.get('Summary') or ''
    if 'notebooklm' in name.lower() or 'notebooklm' in summary.lower():
        matches.append((name, dist.version, summary))
if matches:
    for name, version, summary in sorted(matches):
        print(f'{name}\t{version}\t{summary}')
else:
    print('NO_MATCHING_DISTRIBUTIONS')
PY
  echo
  echo '## CONSOLE_SCRIPTS_CONTAINING_NOTEBOOKLM'
  python - <<'PY'
import importlib.metadata as md
rows = []
for dist in md.distributions():
    dist_name = dist.metadata.get('Name') or ''
    for ep in dist.entry_points:
        if ep.group == 'console_scripts' and 'notebooklm' in ep.name.lower():
            rows.append((dist_name, dist.version, ep.name, ep.value))
if rows:
    for row in sorted(rows):
        print('\t'.join(row))
else:
    print('NO_MATCHING_CONSOLE_SCRIPTS')
PY
  echo
  echo '## COMMAND_V'
  echo -n 'notebooklm='; command -v notebooklm || true
  echo -n 'notebooklm-py='; command -v notebooklm-py || true
  echo
  echo '## CLI_SMOKE'
  if command -v notebooklm >/dev/null 2>&1; then
    echo '$ notebooklm --help'
    notebooklm --help || true
  fi
  if command -v notebooklm-py >/dev/null 2>&1; then
    echo '$ notebooklm-py --help'
    notebooklm-py --help || true
  fi
} | tee "$REPORT_PATH"

printf '\nREPORT=%s\n' "$REPORT_PATH"
