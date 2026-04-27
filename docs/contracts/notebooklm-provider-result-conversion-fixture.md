# NotebookLM Provider-Result Conversion Fixture

Date: 2026-04-25  
Status: synthetic local conversion fixture, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract wires the synthetic captured-result fixture into the normal `notebooklm-provider-result-v0` result shape.

The conversion proves that future redacted `readonly-list` evidence can be represented as a ProviderResult without granting implementation authority.

## Conversion

```text
captured-result fixture -> ProviderResult -> provider-output markdown
```

## Boundary

The conversion is local. It does not:

- run NotebookLM,
- prove auth,
- list real notebooks,
- create implementation facts,
- authorize patches.

## Authority

The converted ProviderResult may be `status: captured`, but that still means provider evidence only.

```text
NotebookLM can inform; local artifacts decide.
```
