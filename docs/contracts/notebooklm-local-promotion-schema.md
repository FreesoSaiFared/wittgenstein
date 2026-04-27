# NotebookLM Local Promotion Schema

Date: 2026-04-25  
Status: local schema skeleton, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract defines the first local promotion artifact schema for NotebookLM provider evidence.

The promotion artifact is local. It is not created by NotebookLM. It is the local system saying, after local verification, that a provider result may be used for a specific target.

## Default stance

The schema skeleton allows executor-context promotion but grants no patch authority by default.

```text
provider evidence -> local verification -> target-specific promotion -> still no patch authority
```

## Patch authority

Patch authority remains explicitly false in this schema version:

```json
"allowsPatchAuthority": false
```

That means even a valid local promotion artifact can allow executor context without allowing patches.

## Authority boundary

Local promotion is target-specific. Provider capture is not promotion. Redaction is not promotion. Conversion is not promotion.

```text
NotebookLM can inform; local artifacts decide.
```
