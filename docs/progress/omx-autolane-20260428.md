# OMX autolane controller note

Date: 2026-04-28
Branch: `feat/nblm/dossier-core`

## Why Codex stopped

Codex completes a single model turn or `omx exec` run when it emits a final handoff. The OMX `UserPromptSubmit` hook can classify a prompt as a heavy multi-step goal, but without an explicit workflow keyword it only injects advisory routing context. That is why the hook says the multi-step goal "did not activate autopilot": triage wrote prompt-routing state, but it did not initialize an active workflow state or launch another Codex turn.

## What activates OMX workflows

Explicit keywords are the deterministic activation surface. The installed keyword registry includes `$autopilot`, `$ralph`, `$team`, `$ultrawork`, `$ralplan`, `$plan`, `$analyze`, and related natural-language aliases. Prompt-side `$autopilot` activates the autopilot skill state for that Codex turn. `omx ralph "task"` is a separate CLI path that launches Codex with Ralph persistence mode active. `omx team` is a tmux/team runtime surface. `omx exec` is non-interactive Codex execution with OMX overlay injection; it still exits after one completed worker turn.

## Repo-local continuation mechanism

`scripts/tarski-autolane.sh` is the repo-local outer controller. It reads `.omx/lane/status.md`, classifies the next lane, generates a packed `$autopilot` Codex prompt, runs one `omx exec` worker cycle, logs the prompt/output under `.omx/lane/logs/`, rereads status, and repeats until a hard stop.

Default safety is conservative: it stops on dirty worktrees, missing status, no clear next lane, force-push/merge/rebase needs, NotebookLM-provider before dossier-core acceptance, external auth/billing/CI blockers, a `.omx/lane/STOP` file, or max iteration exhaustion. Pushing requires `--allow-push`; merging/rebasing and NotebookLM-provider planning require their own explicit flags.

The child `omx exec` call passes `--dangerously-bypass-approvals-and-sandbox` by default because this host's Codex workspace sandbox can fail before shell execution with bubblewrap UID-map errors. The wrapper still keeps its own lane hard stops. Use `--codex-workspace-sandbox` to opt back into the default Codex sandbox, or set `TARSKI_AUTOLANE_OMX_EXEC_ARGS` to override the child `omx exec` flags.

## Usage

Dry-run the next generated prompt:

```bash
scripts/tarski-autolane.sh --dry-run --once
```

Run one local continuation cycle without permitting push:

```bash
scripts/tarski-autolane.sh --once
```

Run the remote-CI continuation lane when pushing the existing PR branch is explicitly allowed:

```bash
scripts/tarski-autolane.sh --allow-push --max-iterations 3
```

Run with the default Codex workspace sandbox instead of the host-specific bypass:

```bash
scripts/tarski-autolane.sh --codex-workspace-sandbox --allow-push --max-iterations 3
```

Stop a running loop cleanly before the next cycle:

```bash
touch .omx/lane/STOP
```

Remove the stop file before restarting:

```bash
rm -f .omx/lane/STOP
```

Logs appear in `.omx/lane/logs/`; authoritative lane state remains `.omx/lane/status.md`.

## Manual boundaries that remain

The helper does not make destructive decisions. Force-push, merge, rebase, external account/billing resolution, and real NotebookLM implementation remain manual or separately authorized lanes. The helper is an outer controller; Codex remains the worker inside each packed cycle.
