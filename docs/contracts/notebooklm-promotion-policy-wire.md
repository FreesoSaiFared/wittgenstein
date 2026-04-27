# NotebookLM Promotion Policy Wire

Date: 2026-04-25  
Status: local policy wiring, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract wires the NotebookLM promotion policy into dossier/provider-output paths.

The key rule is:

```text
NotebookLM provider evidence is planner-only until locally promoted.
```

## Behavior

When `provider=notebooklm`, dossier metadata now records a promotion decision next to the adapter/provider result.

The decision states whether NotebookLM evidence can enter executor context or patch authority. By default, without a separate local promotion artifact, it cannot.

## Provider-output visibility

`provider-output.md` now includes a `Promotion policy decision` section showing:

- target,
- decision OK state,
- executor-context permission,
- patch-authority permission,
- local-promotion requirement,
- blocking errors.

## Authority boundary

Provider capture is not promotion. Conversion is not promotion. Redaction is not promotion.

```text
NotebookLM can inform; local artifacts decide.
```
