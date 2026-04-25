# Dossier codec (local first)

The dossier codec is the first-pass context backend for Wittgenstein's Python prototype surface.

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

## Authority classes

- `implementation_fact`
- `execution_verified_fact`
- `promoted_decision`
- `planning_inference`
- `quarantined_claim`

`executor-context.md` may include only implementation-authorized claims (`implementation_fact`, `execution_verified_fact`, `promoted_decision`). Raw `design_inference` text must not appear there.

## NotebookLM status

NotebookLM is intentionally left as a `NOT_IMPLEMENTED` seam for now. The local provider is the only supported authority-producing path in dossier-core.

## Future target (Level B)

`docs/schemas/patch-plan-ir-v0.json` documents the future PatchPlanIR shape. It is a docs-only target schema and is **not** the current execution path. No compiler or Codex emission path is wired to it yet.
