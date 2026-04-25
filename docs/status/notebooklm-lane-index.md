# NotebookLM Lane Index

Date: 2026-04-25  
Status: documentation-only lane index  
Provider: `notebooklm`

## Purpose

This index maps the NotebookLM provider work into readable lanes: what each lane added, what it protects, and where to look next.

```text
NotebookLM can inform; local artifacts decide.
```

## Lane map

| PR | Lane | Main artifact / contract | Main tests or verifier | Authority effect |
|---:|---|---|---|---|
| 6 | Auth/session failure semantics | NotebookLM auth/session failure notes | Dossier tests | Records failure semantics only |
| 7 | Local-only provider preflight seam | NotebookLM preflight seam | Dossier preflight tests | No NotebookLM execution |
| 8 | Adapter contract | `notebooklm-provider-result-v0` direction | Adapter contract tests | Defines provider seam |
| 9 | Adapter skeleton | Pure local adapter skeleton | `test_notebooklm_adapter.py` | Structured not-ready result |
| 10 | Provider output wire | `provider-output.md` NotebookLM metadata | `test_notebooklm_provider_output_wire.py` | Display only |
| 11 | Manual capture plan | `notebooklm-manual-authenticated-capture-plan.md` | dry-run plan helper | Future plan only |
| 12 | Manual capture runner skeleton | `notebooklm-manual-capture-runner.md` | runner skeleton checks | Refuses live operations |
| 13 | Read-only probe spec | `notebooklm-readonly-probe-spec.md` | spec dry-run | Names `readonly-list` only |
| 14 | Read-only runner gate | `notebooklm-readonly-runner-gate.md` | gate dry-run | Adds explicit gate layer |
| 15 | Live runner dry harness | `notebooklm-live-runner-dry-harness.md` | dry harness checks | Records future command only |
| 16 | Transcript redaction | `notebooklm-transcript-redaction.md` | `test_notebooklm_redaction.py` | Redaction before evidence |
| 17 | Live execution stub | `notebooklm-live-execution-stub.md` | stub transcript routing checks | Proves redaction route |
| 18 | Guarded live runner implementation | `notebooklm-live-runner-guarded.md` | `test_notebooklm_live_runner.py` | Real command path exists but gated |
| 19 | Raw transcript hygiene | `notebooklm-raw-transcript-hygiene.md` | `check_notebooklm_raw_transcripts.sh` | Prevents raw evidence commits |
| 20 | Safety verification gate | `notebooklm-safety-verification-gate.md` | `verify_notebooklm_safety.sh` | Local safety bundle |
| 21 | Captured-result fixture | `notebooklm-captured-result-fixture.md` | `test_notebooklm_captured_fixture.py` | Synthetic fixture only |
| 22 | ProviderResult conversion fixture | `notebooklm-provider-result-conversion-fixture.md` | `test_notebooklm_capture_conversion.py` | Conversion is not promotion |
| 23 | Promotion blocking | `notebooklm-promotion-blocking.md` | `test_notebooklm_promotion_policy.py` | Blocks executor/patch authority |
| 24 | Promotion policy wire | `notebooklm-promotion-policy-wire.md` | `test_notebooklm_promotion_wire.py` | Dossier records planner-only state |
| 25 | All-local verification | `notebooklm-all-local-verification.md` | `verify_notebooklm_all_local.sh` | Full local coherence check |
| 26 | Current-state status | `notebooklm-provider-current-state.md` | all-local verifier | Compact state checkpoint |

## Main files by role

### Safety and gates

- `scripts/check_notebooklm_raw_transcripts.sh`
- `scripts/verify_notebooklm_safety.sh`
- `scripts/verify_notebooklm_all_local.sh`
- `scripts/notebooklm_live_runner_guarded.py`

### Redaction and capture shape

- `polyglot-mini/polyglot/notebooklm_redaction.py`
- `polyglot-mini/polyglot/notebooklm_live_runner.py`
- `polyglot-mini/polyglot/notebooklm_capture_conversion.py`

### Promotion and authority

- `polyglot-mini/polyglot/notebooklm_promotion_policy.py`
- `polyglot-mini/polyglot/dossier.py`

### Status documents

- `docs/status/notebooklm-provider-current-state.md`
- `docs/status/notebooklm-lane-index.md`

## Current invariant set

1. No raw NotebookLM transcript should be committed.
2. Redaction is mandatory before provider evidence storage.
3. ProviderResult conversion is not promotion.
4. Captured NotebookLM evidence is blocked from executor context by default.
5. Executor-context promotion and patch authority are separate gates.
6. All current live-runner execution paths are gated.
7. No merged lane has captured real NotebookLM evidence.

## Green cockpit command

For the full local check:

```bash
scripts/verify_notebooklm_all_local.sh
```

That command writes to `/tmp` by default and should not dirty the worktree.

## Remaining boundary

The first possible real provider touch remains exactly:

```bash
notebooklm list
```

That command still requires explicit human approval and exact gates. This lane does not run it.
