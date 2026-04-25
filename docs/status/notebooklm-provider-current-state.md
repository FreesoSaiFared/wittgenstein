# NotebookLM Provider Current State

Date: 2026-04-25  
Status: local provider path hardened; no live NotebookLM evidence captured  
Provider: `notebooklm`

## One-line state

NotebookLM is now represented as a guarded provider seam whose output can be captured, redacted, converted, and displayed locally, but it cannot enter executor context or patch authority without a separate local promotion artifact.

```text
NotebookLM can inform; local artifacts decide.
```

## What exists now

| Layer | Current state | Authority |
|---|---|---|
| Provider contract | `notebooklm-provider-result-v0` exists | Metadata only |
| Local preflight | Detects package/CLI/storage readiness without calling NotebookLM | No authority |
| Adapter skeleton | Returns structured `not_ready` / unavailable results | No authority |
| Provider output | Renders NotebookLM provider metadata into `provider-output.md` | Provider evidence only |
| Manual capture plan | Documents gated future capture shape | No provider touch |
| Guarded runner | Can execute only behind exact gates; tests use fake runner | Not exercised live |
| Redaction | Local transcript redactor exists and is tested | Hygiene only |
| Raw transcript hygiene | Raw transcripts/cookies/storage are ignored and checked | Prevents evidence contamination |
| Captured fixture | Synthetic captured-result fixture exists | Fixture only |
| ProviderResult conversion | Synthetic fixture converts into ProviderResult | Conversion only |
| Promotion policy | Blocks captured provider evidence by default | Local promotion required |
| Dossier wire | Dossier records promotion decision for NotebookLM | Planner-only until promotion |
| All-local verification | `scripts/verify_notebooklm_all_local.sh` checks the whole local path | Local coherence only |

## Current flow

```text
NotebookLM seam
  -> preflight / adapter result
  -> provider metadata
  -> redacted transcript path when capture exists
  -> ProviderResult
  -> provider-output.md
  -> promotion policy decision
  -> blocked from executor context unless locally promoted
```

## Important boundary

No merged lane so far has performed a real NotebookLM operation.

The repository contains local machinery for a future `readonly-list` probe, but the current committed artifacts are synthetic, dry-run, or local verification artifacts.

## Remaining live-capture boundary

The first possible live operation remains exactly one read-only command:

```bash
notebooklm list
```

That command is not run by this status lane.

A future live probe should preserve these constraints:

- one command only,
- stdout/stderr captured,
- raw transcript kept local and ignored,
- redacted transcript written,
- redaction report written,
- ProviderResult generated from redacted evidence,
- promotion policy applied,
- no executor-context entry without local promotion,
- no patch authority from provider evidence alone.

## Practical next local lanes

1. Add a tiny `docs/status/notebooklm-lane-index.md` that maps PRs/lane names to contracts and tests.
2. Add a verifier summary command that prints a short green/red cockpit status instead of a long log.
3. Add local promotion artifact schema tests, still without allowing patch authority.
4. Only after that, consider the single live `notebooklm list` probe.

## Summary

The codec spine is intact:

```text
source -> provider seam -> redaction -> ProviderResult -> provider-output -> promotion decision -> local artifact authority
```

NotebookLM is now useful as a future context provider, but it is not the core authority mechanism.
