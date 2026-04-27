# Dossier codec (local first)

The dossier codec is the first-pass context backend for Wittgenstein's Python prototype surface. It is the local prototype of a broader **Tarski** idea: an authority runtime that records which evidence may authorize implementation work. The code and CLI names remain `dossier`, `polyglot`, and Wittgenstein-lineage names for now; Tarski is the framework concept, not a package rename in this lane.

The research framing is **Artifact-Deterministic Interfaces**: files are acceptable handoff artifacts only when their authority, provenance, and replay path can be checked mechanically.

## Pipeline

The local path is:

```text
local files
  -> source-ledger.json
  -> claim-ledger.json
  -> planner-context.md
  -> executor-context.md
  -> patch-ledger.json
  -> scope-certificate.json
```

1. `source-ledger.json` captures selected local files, hashes, snippets, and the base git/source snapshot.
2. `claim-ledger.json` turns snippets into claim-addressable authority records.
3. `planner-context.md` may include planning-only material so a planner can reason about tradeoffs.
4. `executor-context.md` filters that material down to implementation-authorized claims.
5. `patch-ledger.json` cites the claims/decisions used by concrete hunks and symbols.
6. `verify-patch-authority` checks the patch ledger against the actual git diff and writes `scope-certificate.json`.

## Current execution path (Level A)

- `polyglot-mini/polyglot/dossier.py` provides a deterministic local provider.
- The provider emits:
  - `source-ledger.json`
  - `claim-ledger.json`
  - `codex-context-pack.json`
  - `planner-context.md`
  - `executor-context.md`
  - `provider-output.md`
  - `manifest.json`
  - `patch-ledger.json`
- `verify-patch-authority` is the hard gate.
- The gate inspects the actual git diff, applies DEC scope sidecar contracts, rejects tainted authority citations, and emits `scope-certificate.json`.
- For Python files under Level A scope, the gate also inspects added/modified top-level imports, functions, and classes, and requires `patch-ledger.json` to account for those symbols.
- DEC sidecars may forbid higher-level capabilities (for example network access) in addition to raw imports/strings.
- OMX hooks are warnings/sentries only; they are not the enforcement boundary.
- Path matching is conservative and repo-root anchored: allowed globs such as `polyglot/*.py` do not authorize nested subdirectories or suffix matches such as `outside/polyglot/*.py`, while forbidden subtree globs such as `packages/*` quarantine descendants.

## Authority classes

- `implementation_fact`
- `execution_verified_fact`
- `promoted_decision`
- `planning_inference`
- `quarantined_claim`

`executor-context.md` may include only implementation-authorized claims (`implementation_fact`, `execution_verified_fact`, `promoted_decision`). Raw `design_inference` text must not appear there.

## What Level A proves

Level A proves that a patch is mechanically tied to:

- the run's base source snapshot,
- implementation-safe claims or promoted decisions,
- an explicit DEC scope contract,
- allowed paths and allowed top-level Python symbol changes,
- absence of configured forbidden imports, strings, and capabilities.

It does **not** prove semantic correctness, product quality, completeness, or safety outside the configured scope contract. Normal tests and review are still required.

## NotebookLM status

NotebookLM is a recognized volatile provider seam, not a core codec or a
second authority path.

- `--provider notebooklm` is accepted by the dossier CLI.
- Dossier-core records provider metadata in `manifest.json`, `provider-output.md`, and the context pack.
- If `notebooklm-py` or a safe CLI path is unavailable/unclear, dossier-core still writes the normal offline artifacts and returns a structured `PROVIDER_UNAVAILABLE` result instead of crashing.
- The exact locally verified contract state is documented in `docs/contracts/notebooklm-py-invocation-contract.md`.
- Replay stays offline and re-renders from captured artifacts; it does not attempt to re-probe NotebookLM.

The local provider remains the only supported authority-producing path today.
A future NotebookLM provider must capture and hash provider output, emit the
same deterministic ledgers, and pass the same patch-authority gate before its
claims can authorize implementation work.

## Future target (Level B)

`docs/schemas/patch-plan-ir-v0.json` documents the future PatchPlanIR shape. It is a docs-only target schema and is **not** the current execution path. No compiler or Codex emission path is wired to it yet.
