#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUT_ROOT="${WITT_NOTEBOOKLM_COCKPIT_OUT:-$(mktemp -d /tmp/witt-notebooklm-cockpit.XXXXXX)}"
VERIFIER_TMP="$(mktemp -d /tmp/witt-notebooklm-cockpit-verifier.XXXXXX)"
mkdir -p "$OUT_ROOT" "$VERIFIER_TMP"

RESULT="$OUT_ROOT/result.json"
VERIFIER_OUT="$VERIFIER_TMP/all-local-verifier"
VERIFIER_STDOUT="$VERIFIER_TMP/all-local-verifier.stdout.txt"
VERIFIER_STDERR="$VERIFIER_TMP/all-local-verifier.stderr.txt"

mkdir -p "$VERIFIER_OUT"

ok=true
status="green"

run_check() {
  local name="$1"
  shift
  if "$@" >/tmp/witt-cockpit-check.out 2>/tmp/witt-cockpit-check.err; then
    printf '  🟢 %s\n' "$name"
  else
    ok=false
    status="red"
    printf '  🔴 %s\n' "$name"
    printf '%s failed\n' "$name" >> "$OUT_ROOT/errors.txt"
    cat /tmp/witt-cockpit-check.out >> "$OUT_ROOT/errors.txt" || true
    cat /tmp/witt-cockpit-check.err >> "$OUT_ROOT/errors.txt" || true
  fi
}

printf 'NotebookLM local cockpit\n'
printf '=======================\n'

run_check "raw transcript hygiene" scripts/check_notebooklm_raw_transcripts.sh
run_check "git diff whitespace" git diff --check

printf '  ⏳ all-local verifier\n'
if WITT_NOTEBOOKLM_ALL_VERIFY_OUT="$VERIFIER_OUT" scripts/verify_notebooklm_all_local.sh >"$VERIFIER_STDOUT" 2>"$VERIFIER_STDERR"; then
  printf '  🟢 all-local verifier\n'
else
  ok=false
  status="red"
  printf '  🔴 all-local verifier\n'
  printf 'all-local verifier failed\n' >> "$OUT_ROOT/errors.txt"
fi

latest_commit="$(git log --oneline -1)"
tracked_raw_count="$(git ls-files 'artifacts/manual-gated/notebooklm/**/transcript.*.raw.txt' 'artifacts/manual-gated/notebooklm/**/raw-provider-output.txt' 'artifacts/manual-gated/notebooklm/**/storage_state.json' 'artifacts/manual-gated/notebooklm/**/cookies*.txt' | wc -l | tr -d ' ')"
notebooklm_test_count="$(find polyglot-mini/tests -maxdepth 1 -type f \( -name 'test_notebooklm*.py' -o -name 'test_dossier.py' \) | wc -l | tr -d ' ')"
notebooklm_schema_count="$(find docs/schemas -type f -name 'notebooklm-*.json' | wc -l | tr -d ' ')"
notebooklm_artifact_json_count="$(find artifacts/manual-gated/notebooklm -type f -name '*.json' | wc -l | tr -d ' ')"

export WITT_COCKPIT_RESULT="$RESULT"
export WITT_COCKPIT_OK="$ok"
export WITT_COCKPIT_STATUS="$status"
export WITT_COCKPIT_LATEST_COMMIT="$latest_commit"
export WITT_COCKPIT_TRACKED_RAW_COUNT="$tracked_raw_count"
export WITT_COCKPIT_TEST_COUNT="$notebooklm_test_count"
export WITT_COCKPIT_SCHEMA_COUNT="$notebooklm_schema_count"
export WITT_COCKPIT_ARTIFACT_JSON_COUNT="$notebooklm_artifact_json_count"
export WITT_COCKPIT_VERIFIER_RESULT="$VERIFIER_OUT/result.json"
export WITT_COCKPIT_VERIFIER_STDOUT="$VERIFIER_STDOUT"
export WITT_COCKPIT_VERIFIER_STDERR="$VERIFIER_STDERR"

python3 - <<'PY'
import json
import os
from pathlib import Path

result = {
    "schemaVersion": "notebooklm-status-cockpit-result-v0",
    "provider": "notebooklm",
    "mode": "status_cockpit",
    "ok": os.environ["WITT_COCKPIT_OK"] == "true",
    "status": os.environ["WITT_COCKPIT_STATUS"],
    "latestCommit": os.environ["WITT_COCKPIT_LATEST_COMMIT"],
    "trackedRawNotebookLMArtifactCount": int(os.environ["WITT_COCKPIT_TRACKED_RAW_COUNT"]),
    "notebooklmTestCount": int(os.environ["WITT_COCKPIT_TEST_COUNT"]),
    "notebooklmSchemaCount": int(os.environ["WITT_COCKPIT_SCHEMA_COUNT"]),
    "notebooklmArtifactJsonCount": int(os.environ["WITT_COCKPIT_ARTIFACT_JSON_COUNT"]),
    "allLocalVerifierResult": os.environ["WITT_COCKPIT_VERIFIER_RESULT"],
    "allLocalVerifierStdout": os.environ["WITT_COCKPIT_VERIFIER_STDOUT"],
    "allLocalVerifierStderr": os.environ["WITT_COCKPIT_VERIFIER_STDERR"],
    "liveNotebookLMExecuted": False,
    "commandsExecuted": [],
    "authority": {
        "mayCreateClaims": False,
        "mayAuthorizeImplementation": False,
        "requiresLocalPromotion": True,
        "providerOutputOnly": True,
    },
}
Path(os.environ["WITT_COCKPIT_RESULT"]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM status cockpit

Compact local status output for the NotebookLM provider path.

Status: \`${status}\`  
OK: \`${ok}\`  
Live NotebookLM executed: \`false\`

Result: \`${RESULT}\`

\`\`\`text
NotebookLM can inform; local artifacts decide.
\`\`\`
MD

printf '\nCockpit status: '
if [ "$ok" = true ]; then
  printf '🟢 GREEN\n'
else
  printf '🔴 RED\n'
fi
printf 'Result: %s\n' "$RESULT"
printf 'Latest: %s\n' "$latest_commit"
printf 'Tracked raw NotebookLM artifacts: %s\n' "$tracked_raw_count"
printf 'NotebookLM tests: %s\n' "$notebooklm_test_count"
printf 'NotebookLM schemas: %s\n' "$notebooklm_schema_count"
printf 'NotebookLM artifact JSON files: %s\n' "$notebooklm_artifact_json_count"

if [ "$ok" != true ]; then
  exit 1
fi
