#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-live-runner-dry-harness}"
OUT_ROOT="${WITT_NOTEBOOKLM_LIVE_DRY_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
OPERATION="${WITT_NOTEBOOKLM_OPERATION:-readonly-list}"
GATE="${WITT_NOTEBOOKLM_MANUAL_GATE:-}"
NOTEBOOKLM_HOME_VALUE="${NOTEBOOKLM_HOME:-}"
READONLY_ENABLE="${WITT_NOTEBOOKLM_ENABLE_READONLY_LIST:-}"
LIVE_ENABLE="${WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION:-}"

EXPECTED_GATE="I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM"
EXPECTED_READONLY_ENABLE="I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY"
EXPECTED_LIVE_ENABLE="I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST"
WOULD_EXECUTE_COMMAND="notebooklm list"

mkdir -p "$OUT_ROOT"

status="blocked"
ok=false
errors_json="[]"
manual_gate_present=false
notebooklm_home_present=false
readonly_enable_present=false
live_enable_present=false

if [ -n "$GATE" ]; then manual_gate_present=true; fi
if [ -n "$NOTEBOOKLM_HOME_VALUE" ]; then notebooklm_home_present=true; fi
if [ -n "$READONLY_ENABLE" ]; then readonly_enable_present=true; fi
if [ -n "$LIVE_ENABLE" ]; then live_enable_present=true; fi

if [ "$OPERATION" != "readonly-list" ]; then
  status="blocked"
  errors_json='[{"code":"NOTEBOOKLM_OPERATION_UNSUPPORTED","message":"Only readonly-list is supported by this dry harness.","blocking":true,"details":{}}]'
elif [ "$GATE" != "$EXPECTED_GATE" ]; then
  status="gate_missing"
  errors_json='[{"code":"NOTEBOOKLM_MANUAL_GATE_MISSING","message":"Manual NotebookLM gate is missing or invalid.","blocking":true,"details":{}}]'
elif [ -z "$NOTEBOOKLM_HOME_VALUE" ]; then
  status="home_missing"
  errors_json='[{"code":"NOTEBOOKLM_HOME_MISSING","message":"NOTEBOOKLM_HOME must be explicit before any future live read-only probe.","blocking":true,"details":{}}]'
elif [ "$READONLY_ENABLE" != "$EXPECTED_READONLY_ENABLE" ]; then
  status="readonly_enable_missing"
  errors_json='[{"code":"NOTEBOOKLM_READONLY_LIST_ENABLE_MISSING","message":"readonly-list remains blocked until the explicit readonly-list enable variable is present.","blocking":true,"details":{}}]'
elif [ "$LIVE_ENABLE" != "$EXPECTED_LIVE_ENABLE" ]; then
  status="live_execution_disabled"
  ok=true
  errors_json='[{"code":"NOTEBOOKLM_LIVE_EXECUTION_DISABLED","message":"All pre-live gates are shaped, but live execution is still disabled by default.","blocking":false,"details":{"required":"WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION"}}]'
else
  status="would_execute_but_stubbed"
  ok=true
  errors_json='[{"code":"NOTEBOOKLM_LIVE_EXECUTION_STUBBED","message":"The final live-execution gate is present, but this dry harness still does not execute NotebookLM.","blocking":false,"details":{"nextLane":"replace stub with one-command execution after explicit approval"}}]'
fi

cat > "$OUT_ROOT/command.txt" <<CMD
${WOULD_EXECUTE_COMMAND}
CMD

cat > "$OUT_ROOT/result.json" <<JSON
{
  "schemaVersion": "notebooklm-live-runner-dry-harness-v0",
  "provider": "notebooklm",
  "mode": "live_runner_dry_harness",
  "status": "${status}",
  "ok": ${ok},
  "experimentId": "${EXPERIMENT_ID}",
  "requestedOperation": "${OPERATION}",
  "wouldExecuteCommand": "${WOULD_EXECUTE_COMMAND}",
  "manualGatePresent": ${manual_gate_present},
  "notebooklmHomePresent": ${notebooklm_home_present},
  "readonlyEnablePresent": ${readonly_enable_present},
  "liveEnablePresent": ${live_enable_present},
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
# NotebookLM live runner dry harness

This artifact was produced by \`scripts/notebooklm_live_runner_dry_harness.sh\`.

It is a dry harness. It does not run NotebookLM.

## Result

- status: ${status}
- ok: ${ok}
- operation: ${OPERATION}
- would execute: \`${WOULD_EXECUTE_COMMAND}\`
- live NotebookLM executed: false

## Full future gate

\`\`\`bash
export WITT_NOTEBOOKLM_MANUAL_GATE=${EXPECTED_GATE}
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=${EXPECTED_READONLY_ENABLE}
export WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION=${EXPECTED_LIVE_ENABLE}
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
\`\`\`

Even with all gates present, this dry harness still does not execute NotebookLM.

NotebookLM can inform; local artifacts decide.
MD

printf 'LIVE_RUNNER_DRY_HARNESS wrote %s/result.json\n' "$OUT_ROOT"
printf 'status=%s ok=%s liveNotebookLMExecuted=false\n' "$status" "$ok"
printf 'No NotebookLM command was executed.\n'

case "$status" in
  gate_missing|home_missing|readonly_enable_missing|blocked)
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
