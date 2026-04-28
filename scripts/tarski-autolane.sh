#!/usr/bin/env bash
set -euo pipefail

# Repo-local OMX/Codex outer controller for Tarski/Wittgenstein lane handoffs.
# It intentionally stays small: classify .omx/lane/status.md, generate the next
# packed Codex prompt, run one `omx exec` worker cycle, then reclassify.

usage() {
  cat <<'USAGE'
Usage: scripts/tarski-autolane.sh [options]

Options:
  --dry-run                    Print the next generated prompt; do not call omx exec.
  --once                       Run at most one lane cycle.
  --max-iterations N           Maximum lane cycles in one invocation (default: 3).
  --allow-push                 Permit prompts that may push the current PR branch.
  --allow-merge                Permit prompts that may merge a PR (default: hard stop).
  --allow-rebase               Permit prompts that may rebase (default: hard stop).
  --allow-notebooklm-provider  Permit planning the NotebookLM-provider lane after acceptance/merge.
  --codex-workspace-sandbox    Do not pass the default child-Codex sandbox bypass flag.
  --allow-dirty                Bypass dirty-worktree hard stop (for dry-run/testing only).
  -h, --help                   Show this help.

Stop:
  touch .omx/lane/STOP         Request a clean stop before the next cycle.
  Ctrl-C                       Stop the currently running controller process.

Logs/status:
  .omx/lane/logs/              Prompt, output, and last-message logs per cycle.
  .omx/lane/status.md          Lane state read before and after every cycle.
USAGE
}

DRY_RUN=0
ONCE=0
ALLOW_PUSH=0
ALLOW_MERGE=0
ALLOW_REBASE=0
ALLOW_NOTEBOOKLM_PROVIDER=0
ALLOW_DIRTY=0
MAX_ITERATIONS="${TARSKI_AUTOLANE_MAX_ITERATIONS:-3}"
OMX_BIN="${OMX_BIN:-omx}"
OMX_EXEC_ARGS_TEXT="${TARSKI_AUTOLANE_OMX_EXEC_ARGS:---dangerously-bypass-approvals-and-sandbox}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --once) ONCE=1 ;;
    --max-iterations)
      shift
      MAX_ITERATIONS="${1:-}"
      ;;
    --allow-push) ALLOW_PUSH=1 ;;
    --allow-merge) ALLOW_MERGE=1 ;;
    --allow-rebase) ALLOW_REBASE=1 ;;
    --allow-notebooklm-provider) ALLOW_NOTEBOOKLM_PROVIDER=1 ;;
    --codex-workspace-sandbox) OMX_EXEC_ARGS_TEXT="" ;;
    --allow-dirty) ALLOW_DIRTY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[tarski-autolane] unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if ! [[ "$MAX_ITERATIONS" =~ ^[0-9]+$ ]] || [[ "$MAX_ITERATIONS" -lt 1 ]]; then
  echo "[tarski-autolane] --max-iterations must be a positive integer" >&2
  exit 2
fi
if [[ "$ONCE" -eq 1 ]]; then
  MAX_ITERATIONS=1
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

STATUS_PATH=".omx/lane/status.md"
STOP_FILE=".omx/lane/STOP"
LOG_DIR=".omx/lane/logs"
mkdir -p "$LOG_DIR"

require_clean_worktree() {
  if [[ "$ALLOW_DIRTY" -eq 1 ]]; then
    return 0
  fi
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "[tarski-autolane] HARD STOP: worktree has uncommitted/untracked changes." >&2
    git status --short >&2 || true
    return 1
  fi
}

read_status() {
  if [[ ! -f "$STATUS_PATH" ]]; then
    echo "[tarski-autolane] HARD STOP: missing $STATUS_PATH; no clear lane state." >&2
    return 1
  fi
  cat "$STATUS_PATH"
}

classify_lane() {
  local status
  status="$(read_status)" || return 1

  if [[ -f "$STOP_FILE" ]]; then
    echo "STOP:user_stop_file"
    return 0
  fi
  if grep -qiE 'remote review-ready|remote-review-ready' <<<"$status"; then
    echo "STOP:remote_review_ready"
    return 0
  fi
  if grep -qiE 'local merge-ready|local_merge-ready|local merge ready' <<<"$status"; then
    if [[ "$ALLOW_PUSH" -eq 1 ]]; then
      echo "LANE:dossier-core-review-remote-ci"
    else
      echo "STOP:push_requires_explicit_permission"
    fi
    return 0
  fi
  if grep -qiE '(dossier-core|pr #[0-9]+).{0,60}(accepted|merged)|accepted and merged|merged.*pr #[0-9]+' <<<"$status"; then
    if [[ "$ALLOW_NOTEBOOKLM_PROVIDER" -eq 1 ]]; then
      echo "LANE:notebooklm-provider-plan"
    else
      echo "STOP:notebooklm_provider_requires_explicit_permission"
    fi
    return 0
  fi
  if grep -qiE 'external (auth|billing|ci|github).*(block|blocked|blocker)|blocked.*(billing|account|auth)' <<<"$status"; then
    echo "STOP:external_auth_billing_or_ci_blocker"
    return 0
  fi
  if grep -qiE 'force push|force-push' <<<"$status"; then
    echo "STOP:force_push_would_be_needed"
    return 0
  fi
  if grep -qiE 'notebooklm-provider.*blocked|notebooklm provider.*blocked' <<<"$status"; then
    echo "STOP:notebooklm_provider_blocked"
    return 0
  fi
  if grep -qiE 'next lane.*dossier-core-review|dossier-core-review independent' <<<"$status"; then
    echo "LANE:dossier-core-review"
    return 0
  fi
  echo "STOP:no_clear_next_lane"
}

build_prompt() {
  local lane status branch head push_policy merge_policy rebase_policy notebooklm_policy
  lane="$1"
  status="$(read_status)"
  branch="$(git branch --show-current 2>/dev/null || echo unknown)"
  head="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
  push_policy="Do not push. Stop and report if pushing would be needed."
  merge_policy="Do not merge PRs."
  rebase_policy="Do not rebase."
  notebooklm_policy="Do not start notebooklm-provider."
  [[ "$ALLOW_PUSH" -eq 1 ]] && push_policy="Push is authorized only for the current branch's existing PR branch if the worktree is clean, the remote branch is expected, and no force push is needed."
  [[ "$ALLOW_MERGE" -eq 1 ]] && merge_policy="Merge is authorized only if the prompt and PR state explicitly make it safe; otherwise stop."
  [[ "$ALLOW_REBASE" -eq 1 ]] && rebase_policy="Rebase is authorized only if necessary, clean, and non-destructive; otherwise stop."
  [[ "$ALLOW_NOTEBOOKLM_PROVIDER" -eq 1 ]] && notebooklm_policy="NotebookLM-provider planning may begin only if dossier-core is accepted/merged; do not implement real NotebookLM unless a later lane explicitly scopes it."

  case "$lane" in
    dossier-core-review-remote-ci)
      cat <<PROMPT
\$autopilot
Activate CALL-PACKING MODE for the lane: dossier-core-review-remote-ci.

You are the worker inside a repo-local OMX lane loop. Complete one packed engineering cycle:
inspect -> plan -> act -> verify -> update .omx/lane/status.md -> choose next safe lane.

Current branch: $branch
Current HEAD: $head
Status source: $STATUS_PATH

Goal for this cycle:
- Inspect git status, remotes, and PR #34.
- Refresh/push the existing PR branch only if safe and permitted below.
- Check/rerun hosted PR checks if possible.
- If CI/auth/billing is externally blocked, record the exact blocker and stop.
- Prepare or update concise PR handoff state.

Safety policy:
- $push_policy
- $merge_policy
- $rebase_policy
- $notebooklm_policy
- Never force push.
- Do not rename packages/CLI/repo.
- Do not implement real NotebookLM.
- Stop on divergent remote, destructive action, unclear dirty worktree, repeated failure, or no clear next lane.

CALL-PACKING output contract:
Final response must be compact: push result, PR #34 status, CI status, files changed, commits, blockers, whether dossier-core is REMOTE REVIEW-READY, exact next lane.

Current lane status:
<status>
$status
</status>
PROMPT
      ;;
    dossier-core-review)
      cat <<PROMPT
\$autopilot
Activate CALL-PACKING MODE for the lane: dossier-core-review.

You are the worker inside a repo-local OMX lane loop. Complete one packed engineering cycle:
inspect -> plan -> edit only if needed -> verify -> commit if safe -> update .omx/lane/status.md -> choose next safe lane.

Current branch: $branch
Current HEAD: $head
Status source: $STATUS_PATH

Goal for this cycle:
- Independently review the latest dossier-core state.
- Fix only small in-scope hardening issues if found.
- Run focused verification.
- Mark LOCAL MERGE-READY if true.

Safety policy:
- $push_policy
- $merge_policy
- $rebase_policy
- $notebooklm_policy
- Do not force push.
- Do not rename packages/CLI/repo.
- Do not implement real NotebookLM.

Current lane status:
<status>
$status
</status>
PROMPT
      ;;
    notebooklm-provider-plan)
      cat <<PROMPT
\$autopilot
Activate CALL-PACKING MODE for the lane: notebooklm-provider-plan.

You are the worker inside a repo-local OMX lane loop. This is planning only unless explicitly authorized by current status.

Current branch: $branch
Current HEAD: $head
Status source: $STATUS_PATH

Goal for this cycle:
- Confirm dossier-core is accepted/merged before any provider lane work.
- If not accepted/merged, update status with the blocker and stop.
- If accepted/merged, prepare a separate notebooklm-provider lane plan only; do not implement real NotebookLM in this run.

Safety policy:
- $push_policy
- $merge_policy
- $rebase_policy
- $notebooklm_policy
- Do not force push.
- Do not rename packages/CLI/repo.

Current lane status:
<status>
$status
</status>
PROMPT
      ;;
    *)
      echo "[tarski-autolane] unsupported lane: $lane" >&2
      return 1
      ;;
  esac
}

run_cycle() {
  local iteration classification kind reason lane ts prompt_file log_file last_file prompt rc
  iteration="$1"
  require_clean_worktree || return 10
  classification="$(classify_lane)" || return 10
  kind="${classification%%:*}"
  reason="${classification#*:}"
  if [[ "$kind" == "STOP" ]]; then
    echo "[tarski-autolane] HARD STOP: $reason"
    return 20
  fi
  lane="$reason"
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  prompt_file="$LOG_DIR/${ts}-iter${iteration}-${lane}.prompt.md"
  log_file="$LOG_DIR/${ts}-iter${iteration}-${lane}.log"
  last_file="$LOG_DIR/${ts}-iter${iteration}-${lane}.last.md"
  prompt="$(build_prompt "$lane")"
  printf '%s\n' "$prompt" > "$prompt_file"
  echo "[tarski-autolane] cycle=$iteration lane=$lane prompt=$prompt_file"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    cat "$prompt_file"
    return 0
  fi
  set +e
  local omx_exec_args=()
  if [[ -n "$OMX_EXEC_ARGS_TEXT" ]]; then
    read -r -a omx_exec_args <<< "$OMX_EXEC_ARGS_TEXT"
  fi
  "$OMX_BIN" exec "${omx_exec_args[@]}" --output-last-message "$last_file" "$prompt" 2>&1 | tee "$log_file"
  rc=${PIPESTATUS[0]}
  set -e
  if [[ "$rc" -ne 0 ]]; then
    echo "[tarski-autolane] HARD STOP: omx exec failed with exit code $rc; log=$log_file" >&2
    return "$rc"
  fi
  if grep -qiE 'HARD STOP|REMOTE REVIEW-READY:[[:space:]]*no|Blocker:' "$last_file" "$log_file" 2>/dev/null; then
    echo "[tarski-autolane] HARD STOP: worker reported a stop/blocker; log=$log_file last=$last_file"
    return 20
  fi
  require_clean_worktree || return 10
  return 0
}

main() {
  if ! command -v "$OMX_BIN" >/dev/null 2>&1; then
    echo "[tarski-autolane] HARD STOP: omx executable not found ($OMX_BIN)." >&2
    exit 10
  fi
  for ((i = 1; i <= MAX_ITERATIONS; i++)); do
    if ! run_cycle "$i"; then
      exit 0
    fi
    if [[ "$DRY_RUN" -eq 1 || "$ONCE" -eq 1 ]]; then
      exit 0
    fi
  done
  echo "[tarski-autolane] HARD STOP: max iterations reached ($MAX_ITERATIONS); inspect $STATUS_PATH before continuing."
}

main "$@"
