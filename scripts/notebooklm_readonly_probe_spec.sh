#!/usr/bin/env bash
set -Eeuo pipefail

EXPERIMENT_ID="${WITT_NOTEBOOKLM_EXPERIMENT_ID:-readonly-probe-spec-dry-run}"
OUT_ROOT="${WITT_NOTEBOOKLM_READONLY_SPEC_OUT:-artifacts/manual-gated/notebooklm/${EXPERIMENT_ID}}"
OPERATION="${WITT_NOTEBOOKLM_OPERATION:-readonly-list}"
GATE="${WITT_NOTEBOOKLM_MANUAL_GATE:-}"
NOTEBOOKLM_HOME_VALUE="${NOTEBOOKLM_HOME:-}"

mkdir -p "$OUT_ROOT"

if [ "$OPERATION" != "readonly-list" ]; then
  echo "Only readonly-list is named by this spec. Got: $OPERATION" >&2
  exit 2
fi

cat > "$OUT_ROOT/request.json" <<JSON
{
  "schemaVersion": "notebooklm-readonly-probe-spec-v0",
  "provider": "notebooklm",
  "mode": "spec_only",
  "operation": "readonly-list",
  "futureCommand": "notebooklm list",
  "approvedNow": false,
  "liveNotebookLMExecuted": false,
  "manualGateRequired": true,
  "manualGatePresent": $([ -n "$GATE" ] && echo true || echo false),
  "notebooklmHomePresent": $([ -n "$NOTEBOOKLM_HOME_VALUE" ] && echo true || echo false),
  "futureGate": {
    "WITT_NOTEBOOKLM_MANUAL_GATE": "I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM",
    "WITT_NOTEBOOKLM_OPERATION": "readonly-list",
    "WITT_NOTEBOOKLM_EXPERIMENT_ID": "manual-auth-capture-YYYYMMDD-HHMMSS",
    "NOTEBOOKLM_HOME": "/tmp/witt-notebooklm-manual-capture-home"
  },
  "forbiddenNow": [
    "notebooklm login",
    "notebooklm list",
    "notebooklm ask",
    "notebooklm create",
    "notebooklm delete",
    "source upload",
    "artifact generation",
    "browser automation",
    "NotebookLMClient.from_storage live call"
  ],
  "futureArtifacts": [
    "request.json",
    "preflight.json",
    "command.txt",
    "transcript.stdout.txt",
    "transcript.stderr.txt",
    "exit-code.txt",
    "redaction-report.json",
    "result.json",
    "README.md"
  ],
  "authority": {
    "mayCreateClaims": false,
    "mayAuthorizeImplementation": false,
    "requiresLocalPromotion": true,
    "providerOutputOnly": true
  }
}
JSON

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM read-only probe spec dry run

This artifact was produced by \`scripts/notebooklm_readonly_probe_spec.sh\`.

It is spec-only. It does not run NotebookLM.

## Named future operation

- operation: \`readonly-list\`
- intended future command: \`notebooklm list\`
- approved now: no
- live NotebookLM executed: false

## Boundary

NotebookLM can inform; local artifacts decide.
MD

printf 'READONLY_PROBE_SPEC wrote %s/request.json\n' "$OUT_ROOT"
printf 'No NotebookLM command was executed.\n'
