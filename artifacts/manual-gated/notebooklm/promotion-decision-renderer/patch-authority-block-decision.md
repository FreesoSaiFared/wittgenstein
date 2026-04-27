# NotebookLM promotion decision

- Provider: `notebooklm`
- Target: `patch_authority`
- OK: `False`
- Can enter executor context: `False`
- Can authorize patch: `False`
- Requires local promotion: `True`
- Provider result status: `captured`

## Authority boundary

- Provider may create claims: `False`
- Provider may authorize implementation: `False`
- Local promotion required: `True`

## Decision errors

- `NOTEBOOKLM_LOCAL_PROMOTION_REQUIRED` Captured NotebookLM provider evidence cannot enter executor context or patch authority without a separate local promotion artifact.

```text
NotebookLM can inform; local artifacts decide.
```
