# NotebookLM Raw Transcript Hygiene Contract

Date: 2026-04-25  
Status: local repository hygiene, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

Raw NotebookLM transcripts may contain cookies, OAuth tokens, session identifiers, account metadata, notebook names, or provider-side diagnostic material. They must not become committed evidence by accident.

The local rule is simple:

```text
Raw transcript may exist locally; redacted transcript may become evidence.
```

## Forbidden committed artifacts

The repository must not commit:

- `artifacts/manual-gated/notebooklm/**/transcript.*.raw.txt`
- `artifacts/manual-gated/notebooklm/**/raw-provider-output.txt`
- `artifacts/manual-gated/notebooklm/**/storage_state.json`
- `artifacts/manual-gated/notebooklm/**/cookies*.txt`
- `.notebooklm/` storage folders under manual-gated artifacts

## Allowed committed artifacts

The repository may commit:

- redacted transcripts,
- redaction reports,
- `command.txt`,
- `result.json`,
- `README.md`,
- schemas,
- contracts,
- progress notes,
- explicit sanitized fixtures.

## Enforcement

`scripts/check_notebooklm_raw_transcripts.sh` fails if forbidden raw NotebookLM artifacts are tracked by git.

## Authority boundary

Even redacted NotebookLM evidence is provider evidence only. It cannot authorize implementation without local promotion.

```text
NotebookLM can inform; local artifacts decide.
```
