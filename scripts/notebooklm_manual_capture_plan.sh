#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-manual-capture-plan-dry-run}"
OUT_ROOT="${WITT_NOTEBOOKLM_PLAN_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
GATE="${WITT_NOTEBOOKLM_MANUAL_GATE:-}"
NOTEBOOKLM_HOME_VALUE="${NOTEBOOKLM_HOME:-}"

mkdir -p "$OUT_ROOT"

cat > "$OUT_ROOT/request.json" <<JSON
{
  "schemaVersion": "notebooklm-manual-capture-plan-v0",
  "provider": "notebooklm",
  "mode": "plan_only",
  "experimentId": "${EXPERIMENT_ID}",
  "manualGateRequired": true,
  "manualGatePresent": $([ -n "$GATE" ] && echo true || echo false),
  "notebooklmHomePresent": $([ -n "$NOTEBOOKLM_HOME_VALUE" ] && echo true || echo false),
  "allowedNow": ["write plan artifacts", "validate manual gate shape", "validate schema", "print future commands without executing them"],
  "forbiddenNow": ["notebooklm login", "notebooklm list", "notebooklm ask", "notebooklm create", "notebooklm delete", "source upload", "artifact generation", "browser automation"],
  "artifactLayout": {
    "root": "${OUT_ROOT}",
    "files": ["request.json", "README.md"]
  },
  "authority": {
    "mayCreateClaims": false,
    "mayAuthorizeImplementation": false,
    "requiresLocalPromotion": true
  }
}
JSON

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM manual capture dry-run plan

This artifact was produced by \`scripts/notebooklm_manual_capture_plan.sh\`.

It is plan-only. It does not run NotebookLM.

## Gate state

- WITT_NOTEBOOKLM_MANUAL_GATE present: $([ -n "$GATE" ] && echo yes || echo no)
- NOTEBOOKLM_HOME present: $([ -n "$NOTEBOOKLM_HOME_VALUE" ] && echo yes || echo no)

## Future explicit gate

\`\`\`bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_EXPERIMENT_ID=manual-auth-capture-YYYYMMDD-HHMMSS
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
\`\`\`

This script still does not execute live NotebookLM commands.
MD

printf 'PLAN_ONLY wrote %s\n' "$OUT_ROOT/request.json"
printf 'No NotebookLM command was executed.\n'
