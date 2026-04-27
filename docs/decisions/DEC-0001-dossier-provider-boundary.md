# DEC-0001 Dossier provider boundary

## Context

The first dossier-core implementation must generate implementation-safe executor context from deterministic local sources. Planning/design inference can guide architecture, but it cannot directly authorize patches.

## Decision

Use a mechanical authority boundary:

- `planner-context.md` may include planning/design inference.
- `executor-context.md` may include only `implementation_fact`, `execution_verified_fact`, and `promoted_decision` claims.
- Any planning inference that needs to justify implementation must first be promoted through a decision artifact or other explicit authority record.
- Patch authority is enforced by deterministic verification against captured context artifacts, not by OMX hooks.
- NotebookLM remains a provider seam only; it is not an authority source until it can emit the same deterministic ledgers and pass the same patch-authority gate.

## Level A scope

The current Level A gate proves provenance and scope, not semantic correctness. It verifies that a patch cites implementation-safe claims or promoted decisions, stays inside the DEC scope sidecar, accounts for modified top-level Python symbols where required, and avoids configured forbidden imports/capabilities. Tests and human review remain responsible for behavior, completeness, and product quality.

## Consequences

The local dossier provider can ship first without NotebookLM, while still producing auditable authority artifacts for implementation work.
