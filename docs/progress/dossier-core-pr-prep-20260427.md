# Dossier-core PR prep

Date: 2026-04-27
Branch: `feat/nblm/dossier-core`
PR: https://github.com/FreesoSaiFared/wittgenstein/pull/34
Current review base included locally: `origin/main` at `9212f1b` and original upstream `p-to-q/wittgenstein` `upstream/main` at `c1a74a0`.

## PR summary draft

- Adds and hardens the local dossier backend as the first concrete Tarski authority-runtime slice.
- Documents the Artifact-Deterministic Interfaces framing and the local pipeline:
  `local files -> source ledger -> claim ledger -> planner context -> executor context -> patch ledger -> scope certificate`.
- Keeps NotebookLM as a volatile provider seam. The CLI may accept `--provider notebooklm`, but the path returns structured unavailable/not-ready metadata and does not authorize implementation work.
- Integrates the latest available original-upstream doctrine/codec updates after conflict-free merge-tree validation.

## Why this matters

Wittgenstein already demonstrates the codec pattern:

```text
prompt -> schema -> validated IR -> renderer/tool/provider -> artifact -> manifest
```

This branch generalizes that pattern toward Tarski for coding-agent work:

```text
source/context -> claim ledger -> authority-filtered executor context -> bounded action -> certificate/manifest
```

The important constraint is that LLM-originated intent is not treated as direct action authority. It must be captured into ledgers, filtered by authority class, constrained by a Patch Scope Contract, and checked by a deterministic Level A gate.

## Commit stack to review

Core dossier/Tarski commits:

1. `6d6e3ff1f1fcb68f8e2e30508a3b734d79997b7d` — Tighten dossier patch scope matching
2. `5d23d87e316d04f8646139ad741342be1865ced1` — Clarify local dossier authority pipeline
3. `f444a0315c408db20f622e7f4bed490462454db5` — Normalize dossier authority docs formatting
4. `37b589fae506f0a04a6c56e44630a2a99764e992` — Anchor dossier scope globs to repo root
5. `c58631d` — Prepare dossier-core PR handoff

Integration commits added after PR creation:

6. `a2072ee` — Integrate upstream NotebookLM seams without widening dossier authority
7. `9db279a` — Bring original upstream doctrine and codec updates into dossier lane
8. `7d0129b` — Keep dossier review handoff current after upstream integration
9. `c73f211` — Record external PR CI blocker in dossier handoff
10. `9d43ab9` — Fix dossier authority review findings

Final local review-hardening after `9d43ab9` keeps the same authority boundary and adds
function-scoped forbidden import-alias coverage for the Level A scanner.

## Surfaces touched

- Python prototype:
  - `polyglot-mini/polyglot/dossier.py`
  - `polyglot-mini/polyglot/cli.py`
  - `polyglot-mini/tests/test_dossier.py`
- NotebookLM seam scaffolding inherited from `origin/main`:
  - `polyglot-mini/polyglot/notebooklm_*.py`
  - `polyglot-mini/tests/test_notebooklm_*.py`
  - `docs/contracts/notebooklm-*.md`
  - `scripts/notebooklm_*.sh`, `scripts/notebooklm_*.py`
- Dossier/Tarski docs and contracts:
  - `docs/codecs/dossier.md`
  - `docs/decisions/DEC-0001-dossier-provider-boundary.md`
  - `docs/decisions/DEC-0001-dossier-provider-boundary.scope.json`
  - `docs/schemas/patch-plan-ir-v0.json`
- Original upstream updates:
  - governance/doctrine docs and guardrails
  - codec-v2 schemas/tests and image codec v2 work
  - audio/image research briefs and maintainer docs

## Current authority contract

Level A checks:

- patch ledger base source snapshot and base git SHA,
- actual git diff files against accounted patch-ledger files,
- cited claims against allowed implementation authority classes,
- cited decisions against DEC scope sidecars,
- allowed and forbidden paths,
- configured forbidden imports, strings, and capabilities,
- added/modified top-level Python symbols when symbol accounting is required.

Level A does **not** prove semantic correctness, product quality, completeness, or safety outside the configured scope contract. Normal tests and review remain required.

## Verification evidence

Passing checks from the post-merge integration pass:

- `PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py` — passed (`22` tests after review-fix regressions and function-scoped import hardening)
- `scripts/verify_notebooklm_all_local.sh` — passed (`59` Python tests plus raw-transcript hygiene, compile, and diff whitespace checks)
- `python3 -m compileall -q ...` for dossier/CLI/NotebookLM Python modules — passed
- Local provider smoke — passed
  - run dir: `artifacts/runs/dossier-20260427T121411Z-3d5fbb0c`
- Offline replay — passed and matched executor context
- Clean fixture with real modified Python function and symbol-accounted patch ledger — passed
  - temp run dir: `/tmp/witt-dossier-verify-post-upstream-c9mv_1j7/artifacts/runs/dossier-20260427T121434Z-ff35ed39`
- `git diff --check` — passed
- `pnpm exec prettier --check docs/codecs/dossier.md docs/decisions/DEC-0001-dossier-provider-boundary.md docs/progress/dossier-core-pr-prep-20260427.md` — passed
- `pnpm typecheck` — passed
- `pnpm test` — passed
- `pnpm format:check:maintained` — passed after upstream merge
- Original upstream check:
  - fetched `upstream/main` from `p-to-q/wittgenstein`
  - `git merge-tree --write-tree HEAD upstream/main` — conflict-free
  - merged `upstream/main` into this branch

## Known unrelated blockers

- Full `pnpm build` still fails in `apps/site` because React and React-DOM versions are mismatched:
  `react-dom@19.2.5` is installed against `react@18.3.1`.
- PR #34 is mergeable, but GitHub Actions did not start required CI jobs because the GitHub account is locked due to a billing issue. This is an external CI availability blocker, not a local test failure.

## Suggested PR checklist state

- Scope / hygiene:
  - Branch is focused on dossier authority plus required upstream integration.
  - No `.omx` runtime noise is included.
  - Generated smoke artifacts remain under ignored `artifacts/runs/`.
- Type:
  - Feature
  - Docs
  - Experimental/RFC boundary for the Tarski authority-runtime concept
- Surfaces:
  - Python (`polyglot-mini/`)
  - Docs / site / meta
- Validation:
  - `pnpm typecheck`
  - `pnpm test`
  - affected Python dossier path
  - NotebookLM all-local verification
  - manifests under `artifacts/runs/<run-id>/`

## Reviewer notes

- Do not review this as a live NotebookLM integration; NotebookLM remains unavailable/not-ready unless separately promoted through deterministic capture and local verification.
- Do review the authority boundary: design inference is planning-only unless promoted through DEC/promotion artifacts.
- Do review the Level A gate as containment/provenance machinery, not as a semantic correctness proof.
- Level B PatchPlanIR remains a docs-only future target.

## Next lane after review

The next lane should be `dossier-core-review` for PR review and authority-contract review.

Only after that should `notebooklm-provider` evaluate a volatile provider behind the same deterministic ledger/certificate boundary.
