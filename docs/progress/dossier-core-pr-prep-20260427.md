# Dossier-core PR prep

Date: 2026-04-27
Branch: `feat/nblm/dossier-core`
Review base observed: `origin/feat/nblm/dossier-core` at `7ce6a175919a08ae46683e41ebf105b8303a5a07`
Prepared HEAD: `37b589fae506f0a04a6c56e44630a2a99764e992`

## PR summary draft

- Adds and hardens the local dossier backend as the first concrete Tarski authority-runtime slice.
- Documents the Artifact-Deterministic Interfaces framing and the local pipeline:
  `local files -> source ledger -> claim ledger -> planner context -> executor context -> patch ledger -> scope certificate`.
- Keeps NotebookLM as a volatile, structured `NOT_IMPLEMENTED` provider seam; no real NotebookLM integration is included.

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

1. `6d6e3ff1f1fcb68f8e2e30508a3b734d79997b7d` — Tighten dossier patch scope matching
2. `5d23d87e316d04f8646139ad741342be1865ced1` — Clarify local dossier authority pipeline
3. `f444a0315c408db20f622e7f4bed490462454db5` — Normalize dossier authority docs formatting
4. `37b589fae506f0a04a6c56e44630a2a99764e992` — Anchor dossier scope globs to repo root

## Surfaces touched

- Python prototype:
  - `polyglot-mini/polyglot/dossier.py`
  - `polyglot-mini/polyglot/cli.py`
  - `polyglot-mini/tests/test_dossier.py`
- Dossier/Tarski docs and contracts:
  - `docs/codecs/dossier.md`
  - `docs/decisions/DEC-0001-dossier-provider-boundary.md`
  - `docs/decisions/DEC-0001-dossier-provider-boundary.scope.json`
  - `docs/schemas/patch-plan-ir-v0.json`

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

Passing checks from the final review pass:

- `PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py` — passed (`14` tests)
- `python3 -m compileall -q polyglot-mini/polyglot/dossier.py polyglot-mini/polyglot/cli.py` — passed
- `python3 -m json.tool docs/decisions/DEC-0001-dossier-provider-boundary.scope.json >/dev/null` — passed
- `python3 -m json.tool docs/schemas/patch-plan-ir-v0.json >/dev/null` — passed
- `git diff --check` — passed
- `pnpm exec prettier --check docs/codecs/dossier.md docs/decisions/DEC-0001-dossier-provider-boundary.md docs/decisions/DEC-0001-dossier-provider-boundary.scope.json docs/schemas/patch-plan-ir-v0.json` — passed
- `pnpm typecheck` — passed
- `pnpm test` — passed
- `pnpm --filter @wittgenstein/cli build` — passed
- `pnpm --filter @wittgenstein/core build` — passed
- `pnpm --filter @wittgenstein-site test` — passed
- Local provider smoke — passed
  - run dir: `artifacts/runs/dossier-20260427T091411Z-f373c554`
- Offline replay — passed
- Empty-diff `verify-patch-authority` — passed
  - scope certificate: `artifacts/runs/dossier-20260427T091411Z-f373c554/scope-certificate.json`
- Clean fixture with real modified Python function and symbol-accounted patch ledger — passed
  - run dir: `artifacts/fixtures/current-clean-gate/repo/artifacts/runs/dossier-20260427T091443Z-69975b3c`

## Known unrelated blockers

- Full `pnpm build` fails in `apps/site` because React and React-DOM versions are mismatched:
  `react-dom@19.2.5` is installed against `react@18.3.1`.
- `pnpm format:check:maintained` fails on pre-existing research brief formatting:
  - `docs/research/briefs/E_benchmarks_v2.md`
  - `docs/research/briefs/F_site_reconciliation.md`
  - `docs/research/briefs/README.md`

These blockers are outside dossier-core and were not fixed in this branch.

## Suggested PR checklist state

- Scope / hygiene:
  - Branch is focused on one change set.
  - No generated artifacts or `.omx` runtime noise are included.
  - Worktree was clean before this PR-prep note.
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
  - manifests under `artifacts/runs/<run-id>/`

## Reviewer notes

- Do not review this as a NotebookLM integration; NotebookLM remains intentionally unavailable.
- Do review the authority boundary: design inference is planning-only unless promoted through DEC/promotion artifacts.
- Do review the Level A gate as containment/provenance machinery, not as a semantic correctness proof.
- Level B PatchPlanIR remains a docs-only future target.

## Next lane after review

If this PR is accepted, the next lane should be `notebooklm-provider` only if the project wants to evaluate a volatile provider behind the same deterministic ledger/certificate boundary. Otherwise, continue strengthening Tarski local authority runtime surfaces before adding external providers.
