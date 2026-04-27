#!/usr/bin/env bash
set -Eeuo pipefail

bad=0

while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    artifacts/manual-gated/notebooklm/*/transcript.*.raw.txt|artifacts/manual-gated/notebooklm/*/raw-provider-output.txt|artifacts/manual-gated/notebooklm/*/storage_state.json|artifacts/manual-gated/notebooklm/*/cookies*.txt)
      echo "FORBIDDEN_RAW_NOTEBOOKLM_ARTIFACT $path" >&2
      bad=1
      ;;
  esac
done < <(git ls-files)

exit "$bad"
