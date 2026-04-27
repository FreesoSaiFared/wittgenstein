#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-readonly-runner-gate-dry-run}"
OUT_ROOT="${WITT_NOTEBOOKLM_READONLY_GATE_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
OPERATION="${WITT_NOTEBOOKLM_OPERATION:-readonly-list}"
GATE="${WITT_NOTEBOOKLM_MANUAL_GATE:-}"
NOTEBOOKLM_HOME_VALUE="${NOTEBOOKLM_HOME:-}"
READONLY_ENABLE="${WITT_NOTEBOOKLM_ENABLE_READONLY_LIST:-}"
EXPECTED_GATE="I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM"
EXPECTED_ENABLE="I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY"

mkdir -p "$OUT_ROOT"

status="blocked"
ok=false
errors_json="[]"
manual_gate_present=false
notebooklm_home_present=false
readonly_enable_present=false

if [ -n "$GATE" ]; then manual_gate_present=true; fi
if [ -n "$NOTEBOOKLM_HOME_VALUE" ]; then notebooklm_home_present=true; fi
if [ -n "$READONLY_ENABLE" ]; then readonly_enable_present=true; fi

if [ "$OPERATION" != "readonly-list" ]; then
  status="blocked"
  errors_json='[{"code":"NOTEBOOKLM_OPERATION_UNSUPPORTED","message":"Only readonly-list is supported by this gate skeleton.","blocking":true,"details":{}}]'
elif [ "$GATE" != "$EXPECTED_GATE" ]; then
  status="gate_missing"
  errors_json='[{"code":"NOTEBOOKLM_MANUAL_GATE_MISSING","message":"Manual NotebookLM gate is missing or invalid.","blocking":true,"details":{}}]'
elif [ -z "$NOTEBOOKLM_HOME_VALUE" ]; then
  status="home_missing"
  errors_json='[{"code":"NOTEBOOKLM_HOME_MISSING","message":"NOTEBOOKLM_HOME must be explicit before any future read-only probe.","blocking":true,"details":{}}]'
elif [ "$READONLY_ENABLE" != "$EXPECTED_ENABLE" ]; then
  status="blocked"
  errors_json='[{"code":"NOTEBOOKLM_READONLY_LIST_ENABLE_MISSING","message":"readonly-list remains blocked until the explicit dry-run enable variable is present.","blocking":true,"details":{"required":"WITT_NOTEBOOKLM_ENABLE_READONLY_LIST"}},{"code":"NOTEBOOKLM_CAPTURE_ABORTED_BY_POLICY","message":"Capture aborted before any NotebookLM command could run.","blocking":true,"details":{}}]'
else
  status="readonly_enabled_not_executed"
  ok=true
  errors_json='[{"code":"NOTEBOOKLM_LIVE_EXECUTION_NOT_IMPLEMENTED","message":"readonly-list gate is satisfied, but this lane still does not execute NotebookLM.","blocking":false,"details":{"nextLane":"implement one-command live runner behind this gate"}}]'
fi

cat > "$OUT_ROOT/result.json" <<JSON
{
  "schemaVersion": "notebooklm-readonly-runner-gate-v0",
  "provider": "notebooklm",
  "mode": "readonly_runner_gate",
  "status": "${status}",
  "ok": ${ok},
  "experimentId": "${EXPERIMENT_ID}",
  "requestedOperation": "${OPERATION}",
  "futureCommand": "notebooklm list",
  "manualGatePresent": ${manual_gate_present},
  "notebooklmHomePresent": ${notebooklm_home_present},
  "readonlyEnablePresent": ${readonly_enable_present},
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
# NotebookLM readonly runner gate dry run

This artifact was produced by \`scripts/notebooklm_readonly_runner_gate.sh\`.

It gates the future \`readonly-list\` operation but still does not run NotebookLM.

## Result

- status: ${status}
- ok: ${ok}
- operation: ${OPERATION}
- future command: \`notebooklm list\`
- live NotebookLM executed: false

## Required future gate

\`\`\`bash
export WITT_NOTEBOOKLM_MANUAL_GATE=${EXPECTED_GATE}
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=${EXPECTED_ENABLE}
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
\`\`\`

Even when satisfied, this script still does not execute NotebookLM.

NotebookLM can inform; local artifacts decide.
MD

printf 'READONLY_RUNNER_GATE wrote %s/result.json\n' "$OUT_ROOT"
printf 'status=%s ok=%s liveNotebookLMExecuted=false\n' "$status" "$ok"
printf 'No NotebookLM command was executed.\n'

if [ "$ok" != true ]; then
  exit 2
fi
