#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -n "${WITT_NOTEBOOKLM_ALL_VERIFY_OUT:-}" ]; then
  OUT_ROOT="$WITT_NOTEBOOKLM_ALL_VERIFY_OUT"
  mkdir -p "$OUT_ROOT"
else
  OUT_ROOT="$(mktemp -d /tmp/witt-notebooklm-all-local.XXXXXX)"
fi

LOG="$OUT_ROOT/verification.log"
RESULT="$OUT_ROOT/result.json"
: > "$LOG"

step() {
  local name="$1"
  shift
  echo "=== $name ===" | tee -a "$LOG"
  "$@" 2>&1 | tee -a "$LOG"
}

step "raw transcript hygiene" scripts/check_notebooklm_raw_transcripts.sh

mapfile -t SCHEMAS < <(find docs/schemas -type f -name 'notebooklm-*.json' | sort)
for schema in "${SCHEMAS[@]}"; do
  step "schema json: $schema" python3 -m json.tool "$schema" >/dev/null
done

mapfile -t ARTIFACT_JSON < <(find artifacts/manual-gated/notebooklm -type f -name '*.json' | sort)
for artifact in "${ARTIFACT_JSON[@]}"; do
  step "artifact json: $artifact" python3 -m json.tool "$artifact" >/dev/null
done

mapfile -t NOTEBOOKLM_MODULES < <(find polyglot-mini/polyglot -maxdepth 1 -type f \( -name 'notebooklm*.py' -o -name 'dossier.py' \) | sort)
mapfile -t NOTEBOOKLM_TESTS < <(find polyglot-mini/tests -maxdepth 1 -type f \( -name 'test_notebooklm*.py' -o -name 'test_dossier.py' \) | sort)

step "python compile: NotebookLM modules and tests" python3 -m py_compile "${NOTEBOOKLM_MODULES[@]}" "${NOTEBOOKLM_TESTS[@]}"

step "notebooklm unittest suite" env PYTHONPATH=polyglot-mini python3 -m unittest -v \
  polyglot-mini/tests/test_dossier.py \
  polyglot-mini/tests/test_notebooklm_adapter.py \
  polyglot-mini/tests/test_notebooklm_provider_output_wire.py \
  polyglot-mini/tests/test_notebooklm_redaction.py \
  polyglot-mini/tests/test_notebooklm_live_runner.py \
  polyglot-mini/tests/test_notebooklm_captured_fixture.py \
  polyglot-mini/tests/test_notebooklm_capture_conversion.py \
  polyglot-mini/tests/test_notebooklm_promotion_policy.py \
  polyglot-mini/tests/test_notebooklm_promotion_wire.py

step "diff whitespace check" git diff --check

python3 - <<PY
import json
from pathlib import Path

result = {
    "schemaVersion": "notebooklm-all-local-verification-result-v0",
    "provider": "notebooklm",
    "mode": "all_local_verification",
    "ok": True,
    "checks": [
        "raw transcript hygiene",
        "NotebookLM schema JSON syntax",
        "NotebookLM artifact JSON syntax",
        "Python compile checks",
        "NotebookLM unittest suite",
        "git diff --check",
    ],
    "schemaCount": ${#SCHEMAS[@]},
    "artifactJsonCount": ${#ARTIFACT_JSON[@]},
    "moduleCount": ${#NOTEBOOKLM_MODULES[@]},
    "testCount": ${#NOTEBOOKLM_TESTS[@]},
    "liveNotebookLMExecuted": False,
    "commandsExecuted": [],
    "logPath": "$LOG",
    "authority": {
        "mayCreateClaims": False,
        "mayAuthorizeImplementation": False,
        "requiresLocalPromotion": True,
        "providerOutputOnly": True,
    },
}
Path("$RESULT").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

cat > "$OUT_ROOT/README.md" <<MD
# NotebookLM all-local verification

This verification run checks the full local NotebookLM safety/conversion/promotion/dossier-wire path.

It does not run NotebookLM.
It does not touch network.
It does not automate a browser.

Result: \`$RESULT\`
Log: \`$LOG\`

\`\`\`text
NotebookLM can inform; local artifacts decide.
\`\`\`
MD

echo "NOTEBOOKLM_ALL_LOCAL_VERIFICATION_OK result=$RESULT log=$LOG"
