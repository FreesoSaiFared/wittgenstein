#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-manual-capture-runner-dry-run}"
OUT_ROOT="${WITT_NOTEBOOKLM_RUNNER_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
GATE="${WITT_NOTEBOOKLM_MANUAL_GATE:-}"
NOTEBOOKLM_HOME_VALUE="${NOTEBOOKLM_HOME:-}"
REQUESTED_OPERATION="${WITT_NOTEBOOKLM_OPERATION:-none}"

mkdir -p "$OUT_ROOT"

manual_gate_present=false
notebooklm_home_present=false
status="plan_only"
ok=true
errors_json="[]"

if [ -n "$GATE" ]; then
  manual_gate_present=true
fi

if [ -n "$NOTEBOOKLM_HOME_VALUE" ]; then
  notebooklm_home_present=true
fi

if [ "$manual_gate_present" != true ]; then
  status="gate_missing"
  ok=false
  errors_json='[{"code":"NOTEBOOKLM_MANUAL_GATE_MISSING","message":"Manual NotebookLM gate is not present.","blocking":true,"details":{}}]'
elif [ "$notebooklm_home_present" != true ]; then
  status="home_missing"
  ok=false
  errors_json='[{"code":"NOTEBOOKLM_HOME_MISSING","message":"NOTEBOOKLM_HOME is not set for the manual capture runner.","blocking":true,"details":{}}]'
elif [ "$REQUESTED_OPERATION" != "none" ] && [ "$REQUESTED_OPERATION" != "plan-only" ]; then
  status="blocked"
  ok=false
  errors_json='[{"code":"NOTEBOOKLM_LIVE_OPERATION_DISABLED","message":"A live NotebookLM operation was requested, but this skeleton runner forbids live operations.","blocking":true,"details":{"liveOperationsEnabled":false}},{"code":"NOTEBOOKLM_CAPTURE_ABORTED_BY_POLICY","message":"Capture aborted before any NotebookLM command could run.","blocking":true,"details":{}}]'
fi

cat > "$OUT_ROOT/request.json" <<JSON
{
  "schemaVersion": "notebooklm-manual-capture-runner-result-v0",
  "provider": "notebooklm",
  "mode": "runner_skeleton",
  "experimentId": "${EXPERIMENT_ID}",
  "requestedOperation": "${REQUESTED_OPERATION}",
  "manualGatePresent": ${manual_gate_present},
  "notebooklmHomePresent": ${notebooklm_home_present},
  "liveOperationsEnabled": false,
  "allowedNow": ["write local runner artifacts", "classify gate/home/operation state"],
  "forbiddenNow": ["notebooklm login", "notebooklm list", "notebooklm ask", "notebooklm create", "notebooklm delete", "source upload", "artifact generation", "browser automation"]
}
JSON

cat > "$OUT_ROOT/result.json" <<JSON
{
  "schemaVersion": "notebooklm-manual-capture-runner-result-v0",
  "provider": "notebooklm",
  "mode": "runner_skeleton",
  "status": "${status}",
  "ok": ${ok},
  "experimentId": "${EXPERIMENT_ID}",
  "requestedOperation": "${REQUESTED_OPERATION}",
  "manualGatePresent": ${manual_gate_present},
  "notebooklmHomePresent": ${notebooklm_home_present},
  "liveNotebookLMExecuted": false,
  "commandsExecuted": [],
  "errors": ${errors_json},
  "authority": {
    "mayCreateClaims": false,
    "mayAuthorizeImplementation": false,
    "requiresLocalPromotion": true,
    "providerOutputOnly": true
  }
}
JSON

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM manual capture runner skeleton

This artifact was produced by \`scripts/notebooklm_manual_capture_runner.sh\`.

It is a skeleton runner. It does not run NotebookLM.

## Result

- status: ${status}
- ok: ${ok}
- requested operation: ${REQUESTED_OPERATION}
- live NotebookLM executed: false

## Boundary

NotebookLM can inform; local artifacts decide.
MD

printf 'RUNNER_SKELETON wrote %s/result.json\n' "$OUT_ROOT"
printf 'No NotebookLM command was executed.\n'

if [ "$ok" != true ]; then
  exit 2
fi
