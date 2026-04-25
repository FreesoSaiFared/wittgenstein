# NotebookLM readonly runner gate dry run

This artifact was produced by `scripts/notebooklm_readonly_runner_gate.sh`.

It gates the future `readonly-list` operation but still does not run NotebookLM.

## Result

- status: readonly_enabled_not_executed
- ok: true
- operation: readonly-list
- future command: `notebooklm list`
- live NotebookLM executed: false

## Required future gate

```bash
export WITT_NOTEBOOKLM_MANUAL_GATE=I_UNDERSTAND_THIS_TOUCHES_REAL_NOTEBOOKLM
export WITT_NOTEBOOKLM_ENABLE_READONLY_LIST=I_EXPLICITLY_ENABLE_READONLY_LIST_DRY_RUN_ONLY
export WITT_NOTEBOOKLM_OPERATION=readonly-list
export NOTEBOOKLM_HOME=/tmp/witt-notebooklm-manual-capture-home
```

Even when satisfied, this script still does not execute NotebookLM.

NotebookLM can inform; local artifacts decide.
