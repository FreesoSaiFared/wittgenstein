# NotebookLM Local Promotion Validation

Date: 2026-04-25  
Status: local validation, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract tightens local promotion from a document-shaped convention into a code-level validation step.

The rule is:

```text
No local promotion artifact is trusted until code-level validation passes.
```

## Validation checks

The validator checks:

- schema version,
- provider,
- source ProviderResult contract,
- allowed target list,
- no patch-authority target smuggling,
- `allowsPatchAuthority: false`,
- `localVerification.status: verified`,
- non-empty `method`,
- non-empty `verifiedBy`,
- exact authority boundary fields.

## Patch authority

Patch authority remains forbidden in NotebookLM local promotion v0.

Executor-context promotion can be valid. Patch authority cannot.

## Authority boundary

Provider capture is not promotion. Conversion is not promotion. Redaction is not promotion. Validation is not patch authority.

```text
NotebookLM can inform; local artifacts decide.
```
