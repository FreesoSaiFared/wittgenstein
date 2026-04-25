#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUT_ROOT="${WITT_NOTEBOOKLM_SAFETY_VERIFY_OUT:-artifacts/manual-gated/notebooklm/safety-verification-gate-dry-run}"
mkdir -p "$OUT_ROOT"

STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LOG="$OUT_ROOT/verification.log"
RESULT="$OUT_ROOT/result.json"

: > "$LOG"

run_step() {
  local name="$1"
  shift
  echo "=== $name ===" | tee -a "$LOG"
  "$@" 2>&1 | tee -a "$LOG"
}

run_step "raw transcript hygiene" scripts/check_notebooklm_raw_transcripts.sh

SCHEMAS=(docs/schemas/notebooklm-*.json)
if [ -e "${SCHEMAS[0]}" ]; then
  for schema in "${SCHEMAS[@]}"; do
    run_step "json schema syntax: $schema" python3 -m json.tool "$schema" >/dev/null
  done
fi

run_step "notebooklm unittest suite" env PYTHONPATH=polyglot-mini python3 -m unittest -v \
  polyglot-mini/tests/test_dossier.py \
  polyglot-mini/tests/test_notebooklm_adapter.py \
  polyglot-mini/tests/test_notebooklm_provider_output_wire.py \
  polyglot-mini/tests/test_notebooklm_redaction.py \
  polyglot-mini/tests/test_notebooklm_live_runner.py

run_step "diff whitespace check" git diff --check

FINISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$RESULT" <<JSON
{
  "schemaVersion": "notebooklm-safety-verification-result-v0",
  "provider": "notebooklm",
  "mode": "safety_verification_gate",
  "ok": true,
  "startedAt": "${STARTED_AT}",
  "finishedAt": "${FINISHED_AT}",
  "checks": [
    "raw transcript hygiene",
    "notebooklm schema JSON syntax",
    "NotebookLM unittest suite",
    "git diff --check"
  ],
  "liveNotebookLMExecuted": false,
  "commandsExecuted": [],
  "logPath": "${LOG}",
  "authority": {
    "mayCreateClaims": false,
    "mayAuthorizeImplementation": false,
    "requiresLocalPromotion": true,
    "providerOutputOnly": true
  }
}
JSON

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM safety verification gate dry run

This artifact was produced by \`scripts/verify_notebooklm_safety.sh\`.

It runs local safety checks only.

## Checks

- raw transcript hygiene
- NotebookLM schema JSON syntax
- NotebookLM-related unit tests
- \`git diff --check\`

Live NotebookLM executed: false.

NotebookLM can inform; local artifacts decide.
MD

echo "NOTEBOOKLM_SAFETY_VERIFICATION_OK result=$RESULT"
