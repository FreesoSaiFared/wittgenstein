# NotebookLM manual capture dry-run plan

This artifact was produced by `scripts/notebooklm_manual_capture_plan.sh`.

It is plan-only. It does not run NotebookLM.

## Gate state

- WITT_NOTEBOOKLM_MANUAL_GATE present: no
- NOTEBOOKLM_HOME present: no

## Future explicit gate

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_EXPERIMENT_ID=manual-auth-capture-YYYYMMDD-HHMMSS
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

This script still does not execute live NotebookLM commands.
