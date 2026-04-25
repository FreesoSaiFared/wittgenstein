# DEC-0001 Dossier provider boundary

## Context
The first dossier-core implementation must generate implementation-safe executor context from deterministic local sources. Planning/design inference can guide architecture, but it cannot directly authorize patches.

## Decision
Use a mechanical authority boundary:
- `planner-context.md` may include planning/design inference.
- `executor-context.md` may include only `implementation_fact`, `execution_verified_fact`, and `promoted_decision` claims.
- Any planning inference that needs to justify implementation must first be promoted through a decision artifact or other explicit authority record.
- Patch authority is enforced by deterministic verification against captured context artifacts, not by OMX hooks.

## Consequences
- The local dossier provider can ship first without NotebookLM, while still producing auditable authority artifacts for implementation work.
- `notebooklm` may exist as a provider selector and metadata seam, but it must not become a second authority path or a core codec.
- If NotebookLM is unavailable or lacks a verified non-network invocation path, dossier-core must return a structured unavailable result while preserving the same offline replayable artifact spine.
