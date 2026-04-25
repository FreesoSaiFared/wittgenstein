#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-live-execution-stub}"
OUT_ROOT="${WITT_NOTEBOOKLM_LIVE_STUB_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
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
manual_gate_present=false
notebooklm_home_present=false
readonly_enable_present=false
live_enable_present=false
errors_json="[]"

if [ -n "$GATE" ]; then manual_gate_present=true; fi
if [ -n "$NOTEBOOKLM_HOME_VALUE" ]; then notebooklm_home_present=true; fi
if [ -n "$READONLY_ENABLE" ]; then readonly_enable_present=true; fi
if [ -n "$LIVE_ENABLE" ]; then live_enable_present=true; fi

if [ "$OPERATION" != "readonly-list" ]; then
  status="blocked"
  errors_json='[{"code":"NOTEBOOKLM_OPERATION_UNSUPPORTED","message":"Only readonly-list is supported by this live execution stub.","blocking":true,"details":{}}]'
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
  status="stubbed_transcript_redacted"
  ok=true
  errors_json='[{"code":"NOTEBOOKLM_LIVE_EXECUTION_STUBBED","message":"The final live-execution gate is present, but this stub still does not execute NotebookLM. It proves transcript routing through redaction.","blocking":false,"details":{"nextLane":"replace stubbed transcript generation with one-command live execution after explicit approval"}}]'
fi

cat > "$OUT_ROOT/command.txt" <<CMD
${WOULD_EXECUTE_COMMAND}
CMD

cat > "$OUT_ROOT/transcript.stdout.raw.txt" <<TXT
NOTEBOOKLM LIVE EXECUTION STUB
status=${status}
wouldExecute=${WOULD_EXECUTE_COMMAND}
liveNotebookLMExecuted=false
Authorization: Bearer stubbed_demo_token_abcdefghijklmnopqrstuvwxyz1234567890
Cookie: SID=stubbed_sid_value; __Secure-1PSID=stubbed_secure_cookie_value
NotebookLM can inform; local artifacts decide.
TXT

cat > "$OUT_ROOT/transcript.stderr.raw.txt" <<TXT
NOTEBOOKLM LIVE EXECUTION STUB STDERR
No NotebookLM command was executed.
access_token=stubbed_demo_access_token_value
TXT

scripts/notebooklm_redact_transcript.py \
  --input "$OUT_ROOT/transcript.stdout.raw.txt" \
  --output "$OUT_ROOT/transcript.stdout.redacted.txt" \
  --report "$OUT_ROOT/redaction-report.stdout.json" >/dev/null

scripts/notebooklm_redact_transcript.py \
  --input "$OUT_ROOT/transcript.stderr.raw.txt" \
  --output "$OUT_ROOT/transcript.stderr.redacted.txt" \
  --report "$OUT_ROOT/redaction-report.stderr.json" >/dev/null

cat > "$OUT_ROOT/result.json" <<JSON
{
  "schemaVersion": "notebooklm-live-execution-stub-v0",
  "provider": "notebooklm",
  "mode": "live_execution_stub",
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
  "rawTranscriptPaths": [
    "${OUT_ROOT}/transcript.stdout.raw.txt",
    "${OUT_ROOT}/transcript.stderr.raw.txt"
  ],
  "redactedTranscriptPaths": [
    "${OUT_ROOT}/transcript.stdout.redacted.txt",
    "${OUT_ROOT}/transcript.stderr.redacted.txt"
  ],
  "redactionReportPaths": [
    "${OUT_ROOT}/redaction-report.stdout.json",
    "${OUT_ROOT}/redaction-report.stderr.json"
  ],
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
# NotebookLM live execution stub

This artifact was produced by \`scripts/notebooklm_live_execution_stub.sh\`.

It does not run NotebookLM.

It proves that any future transcript path has a mandatory redaction route before provider evidence can be stored.

## Result

- status: ${status}
- ok: ${ok}
- operation: ${OPERATION}
- would execute: \`${WOULD_EXECUTE_COMMAND}\`
- live NotebookLM executed: false

## Transcript route

\`\`\`text
raw transcript -> scripts/notebooklm_redact_transcript.py -> redacted transcript + redaction report -> provider evidence
\`\`\`

NotebookLM can inform; local artifacts decide.
MD

printf 'LIVE_EXECUTION_STUB wrote %s/result.json\n' "$OUT_ROOT"
printf 'status=%s ok=%s liveNotebookLMExecuted=false\n' "$status" "$ok"
printf 'Transcript redaction route executed on stub transcripts.\n'
printf 'No NotebookLM command was executed.\n'

case "$status" in
  gate_missing|home_missing|readonly_enable_missing|blocked)
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
