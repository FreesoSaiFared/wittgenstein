# NotebookLM live runner dry harness

This artifact was produced by `scripts/notebooklm_live_runner_dry_harness.sh`.

It is a dry harness. It does not run NotebookLM.

## Result

- status: would_execute_but_stubbed
- ok: true
- operation: readonly-list
- would execute: `notebooklm list`
- live NotebookLM executed: false

## Full future gate

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION=I_EXPLICITLY_ENABLE_ONE_LIVE_READONLY_NOTEBOOKLM_LIST
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

Even with all gates present, this dry harness still does not execute NotebookLM.

NotebookLM can inform; local artifacts decide.
