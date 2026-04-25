# NotebookLM status cockpit status

Date: 2026-04-25  
Branch: `feat/nblm/notebooklm-status-cockpit`

## Goal

Add a compact green/red cockpit command for NotebookLM status output.

## Result

Added:

- `scripts/notebooklm_status_cockpit.sh`
- `docs/contracts/notebooklm-status-cockpit.md`
- `docs/progress/notebooklm-status-cockpit-status.md`
- dry-run artifact under `artifacts/manual-gated/notebooklm/status-cockpit/`

## Behavior

The cockpit runs local checks and prints a compact status summary.

It executes no NotebookLM command.

## Next lane

Add a local promotion artifact schema skeleton, still granting no patch authority by default.
