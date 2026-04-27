# NotebookLM Transcript Redaction Contract

Date: 2026-04-25  
Status: local-only redaction utility, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

Before any future authenticated NotebookLM transcript can become provider evidence, it must pass through a local redaction step.

This contract defines the first transcript redaction layer for future NotebookLM capture artifacts. It does not run NotebookLM, refresh auth, inspect notebooks, or touch network.

## Redaction target

The redactor is designed for future files such as:

```text
transcript.stdout.txt
transcript.stderr.txt
raw-provider-output.txt
```

## Redacted classes

The redactor removes or masks:

- HTTP bearer authorization values
- Cookie and Set-Cookie header contents
- common token fields such as access_token, refresh_token, id_token, csrf_token, session_id
- URL secret parameters such as code= or token=
- common Google secure cookie names
- long opaque credential-like strings

Default rule: if unsure, redact.

## Report shape

The redactor writes a report with:

- `schemaVersion`
- input and output SHA-256 values
- total redaction count
- per-rule counts
- authority boundary fields

## Authority boundary

A redacted transcript is still provider evidence only.

It may not directly create implementation facts, execution-verified facts, patch authority, or promotion authority.

```text
NotebookLM can inform; local artifacts decide.
```
