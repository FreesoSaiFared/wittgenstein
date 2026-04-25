#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

FORMAT="text"
if [ "${1:-}" = "--json" ]; then
  FORMAT="json"
elif [ "${1:-}" = "--text" ] || [ -z "${1:-}" ]; then
  FORMAT="text"
else
  echo "usage: scripts/list_notebooklm_promotion_decisions.sh [--text|--json]" >&2
  exit 2
fi

BASE="artifacts/manual-gated/notebooklm/promotion-decision-renderer"
mapfile -t paths < <(find "$BASE" -type f -name '*decision.md' 2>/dev/null | sort)

if [ "$FORMAT" = "json" ]; then
  python3 - "$BASE" "${paths[@]}" <<'PY'
from __future__ import annotations

import json
import sys

base = sys.argv[1]
paths = sys.argv[2:]
result = {
    "schemaVersion": "notebooklm-promotion-decision-paths-v0",
    "provider": "notebooklm",
    "mode": "promotion_decision_paths",
    "ok": True,
    "basePath": base,
    "count": len(paths),
    "paths": paths,
    "liveNotebookLMExecuted": False,
    "commandsExecuted": [],
    "authority": {
        "mayCreateClaims": False,
        "mayAuthorizeImplementation": False,
        "requiresLocalPromotion": True,
        "providerOutputOnly": True,
    },
}
print(json.dumps(result, indent=2, sort_keys=True))
PY
  exit 0
fi

printf 'NotebookLM rendered promotion decisions\n'
printf '=======================================\n'
printf 'Count: %s\n' "${#paths[@]}"
if [ "${#paths[@]}" -eq 0 ]; then
  printf 'No rendered promotion decision Markdown files found.\n'
else
  for path in "${paths[@]}"; do
    printf '%s\n' "$path"
  done
fi
