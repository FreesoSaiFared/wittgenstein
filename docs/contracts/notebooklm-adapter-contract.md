# NotebookLM Adapter Contract

Date: 2026-04-25  
Status: contract-only, no live adapter  
Provider: `notebooklm`  
Contract version: `notebooklm-provider-result-v0`

## Purpose

This contract defines the smallest safe boundary for a future NotebookLM provider adapter in Wittgenstein.

NotebookLM remains a volatile provider/backend. It is not a core codec, not a local verifier, and not an implementation-authority path. Its output may be captured, quoted, inspected, and later promoted through local artifacts, but it may not directly authorize code changes.

The adapter exists to turn a NotebookLM interaction into a reproducible provider result:

```text
ProviderRequest -> NotebookLM provider call/capture -> ProviderResult -> provider-output.md -> local claim/promotion process
```

The adapter must preserve the dossier spine:

```text
source ledger -> provider output -> claim ledger -> planner context -> executor context -> patch ledger -> scope certificate
```

## Inputs already verified

The following facts are documented by earlier lanes:

- Install target: `notebooklm-py`.
- Python import target: `notebooklm`.
- Client import target: `notebooklm.client`.
- CLI executable: `notebooklm`.
- Safe smoke command: `notebooklm --help`.
- Auth storage default: `~/.notebooklm/storage_state.json`.
- `NOTEBOOKLM_HOME` changes the storage home.
- `notebooklm status` is not an auth gate.
- `notebooklm auth check` can exit `0` while reporting auth failures.
- `notebooklm list` exits nonzero with `Not logged in.` when storage/auth is absent.
- `NotebookLMClient.from_storage()` gives a cleaner missing-storage failure than CLI status checks.

## ProviderRequest shape

A future adapter must receive a ProviderRequest-like object with only deliberate fields:

```json
{
  "contractVersion": "notebooklm-provider-result-v0",
  "provider": "notebooklm",
  "runId": "dossier-...",
  "task": "natural language task",
  "workspaceRoot": "/absolute/path",
  "workingDirectory": "/absolute/path",
  "baseGitSha": "optional git sha",
  "baseSourceSnapshot": "sha256-like source snapshot",
  "sourceLedgerPath": "artifacts/runs/.../source-ledger.json",
  "claimLedgerPath": "artifacts/runs/.../claim-ledger.json",
  "requestedOutPath": "requested output path",
  "constraints": {
    "noImplementationAuthority": true,
    "offlineReplayRequired": true,
    "allowNotebookMutation": false,
    "allowNotebookCreation": false,
    "allowNotebookDeletion": false
  }
}
```

### Request rules

The request may include source metadata and source-ledger paths. It must not silently upload arbitrary repository contents. Any source text sent to NotebookLM must be explicitly represented in provider metadata and reproducible from the local source ledger.

The request must carry enough metadata for local replay to know that NotebookLM was used, but replay must not call NotebookLM again.

## ProviderResult shape

A future adapter must return a ProviderResult-like object:

```json
{
  "contractVersion": "notebooklm-provider-result-v0",
  "provider": "notebooklm",
  "status": "not_ready | unavailable | failed | captured",
  "ok": false,
  "runId": "dossier-...",
  "requestId": "optional adapter request id",
  "preflight": {},
  "capture": {
    "mode": "none | cli | python_api | manual_export",
    "notebookId": null,
    "notebookTitle": null,
    "operation": null,
    "capturedAt": null,
    "rawTextPath": null,
    "metadataPath": null
  },
  "errors": [
    {
      "code": "NOTEBOOKLM_READY_UNVERIFIED",
      "message": "NotebookLM adapter is not wired for live capture.",
      "details": {}
    }
  ],
  "authority": {
    "mayCreateClaims": false,
    "mayAuthorizeImplementation": false,
    "requiresLocalPromotion": true
  }
}
```

## Status values

| Status | Meaning |
|---|---|
| `unavailable` | Required package, CLI, or import target is absent. |
| `not_ready` | Local tooling is present but auth/capture/adapter readiness is unverified. |
| `failed` | A real adapter attempt was made and failed in a classified way. |
| `captured` | A real adapter captured NotebookLM output, but the output is still provider evidence only. |

`captured` does not mean implementation authority. It only means NotebookLM output was successfully recorded.

## Error taxonomy

The adapter and preflight layer should use stable error codes. Current codes include:

- `NOTEBOOKLM_PACKAGE_MISSING`
- `NOTEBOOKLM_CLI_MISSING`
- `NOTEBOOKLM_STORAGE_MISSING`
- `NOTEBOOKLM_AUTH_UNVERIFIED`
- `NOTEBOOKLM_READY_UNVERIFIED`

Additional adapter-level codes should be introduced only when a concrete runtime case is observed:

- `NOTEBOOKLM_ADAPTER_NOT_WIRED`
- `NOTEBOOKLM_AUTH_STORAGE_INVALID`
- `NOTEBOOKLM_AUTH_REFRESH_FAILED`
- `NOTEBOOKLM_NOTEBOOK_NOT_SELECTED`
- `NOTEBOOKLM_OPERATION_UNSUPPORTED`
- `NOTEBOOKLM_CAPTURE_FAILED`
- `NOTEBOOKLM_OUTPUT_EMPTY`
- `NOTEBOOKLM_OUTPUT_UNTRUSTED`

## provider-output.md capture rules

`provider-output.md` is the human-readable provider evidence file. It must include:

1. Provider name and contract version.
2. Status and error summary.
3. Preflight metadata.
4. Capture mode, if any.
5. Notebook identity, if used and safe to record.
6. Raw output location, if captured.
7. Explicit authority warning.

The file must say, in plain language, whether NotebookLM output is:

- absent,
- unavailable,
- not ready,
- captured but unpromoted,
- or locally promoted later by a separate artifact.

## Manifest metadata rules

`manifest.json` and provider metadata should include:

```json
{
  "provider": "notebooklm",
  "providerMetadata": {
    "provider": "notebooklm",
    "status": "not_ready",
    "contractVersion": "notebooklm-provider-result-v0",
    "preflight": {},
    "adapterResult": {},
    "errors": []
  }
}
```

The manifest must not report `ok: true` for `provider=notebooklm` until a real adapter is implemented and the local dossier pipeline has decided what successful provider capture means. Even then, successful provider capture is not the same as implementation authority.

## Claim boundary

NotebookLM output may support these local claim classes only after local processing:

- `provider_observation`
- `research_context`
- `planning_inference`

NotebookLM output must not directly produce:

- `implementation_fact`
- `execution_verified_fact`
- patch authority
- scope authority
- promotion authority

Any future promotion from NotebookLM output to implementation-relevant material requires a local promotion artifact, such as a DEC file, claim-ledger promotion entry, or verifier output.

## Replay constraints

Replay must remain offline.

A replay may read:

- `manifest.json`
- `provider-output.md`
- `source-ledger.json`
- `claim-ledger.json`
- `codex-context-pack.json`
- captured raw provider files already stored in the run directory

A replay must not:

- call NotebookLM,
- refresh auth,
- run CLI commands,
- hit network APIs,
- recreate provider state.

## Adapter implementation implications

The first real adapter should be deliberately small:

1. Run local preflight.
2. Classify auth/storage readiness.
3. Attempt only a read-only, explicitly gated capture operation.
4. Write provider result and raw capture files.
5. Return structured status.
6. Leave claim promotion to local dossier code.

The adapter should prefer Python API calls over CLI wrapping only if auth/session behavior is verified. Until then, the CLI and Python API are both discovery surfaces, not trusted runtime surfaces.

## Non-goals

This contract does not authorize:

- browser automation,
- automatic NotebookLM notebook creation,
- automatic deletion or mutation,
- uploading whole repositories without explicit source-ledger representation,
- treating NotebookLM as a source of implementation authority,
- treating NotebookLM output as replayable unless already captured locally.

## Decision

NotebookLM may become a provider. It must not become a hidden authority path.

The implementation rule is:

```text
NotebookLM can inform; local artifacts decide.
```
