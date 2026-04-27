# NotebookLM Promotion-Blocking Contract

Date: 2026-04-25  
Status: local promotion policy, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

Captured NotebookLM provider evidence must not silently become executor context, claim authority, implementation authority, or patch authority.

This contract adds an explicit local promotion policy:

```text
captured provider evidence -> blocked by default -> local promotion artifact required
```

## Default rule

A NotebookLM ProviderResult with `status: captured` is still provider evidence only.

Without a separate local promotion artifact, it must be blocked from:

- executor context,
- claim creation,
- implementation authority,
- patch authority.

## Local promotion artifact

A future local promotion artifact must include:

- `schemaVersion: notebooklm-local-promotion-v0`
- `provider: notebooklm`
- `localVerification.status: verified`
- an explicit target in `allowedTargets`

Executor-context promotion and patch-authority promotion are separate. Allowing executor context does not imply patch authority.

## Authority boundary

Provider capture is not promotion.
Conversion is not promotion.
Redaction is not promotion.

```text
NotebookLM can inform; local artifacts decide.
```
