# NotebookLM Status Cockpit Contract

Date: 2026-04-25  
Status: local status command, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract defines a compact green/red cockpit command for the local NotebookLM provider path.

```bash
scripts/notebooklm_status_cockpit.sh
```

The cockpit is intentionally local. It does not run NotebookLM, touch network, refresh auth, or automate a browser.

## Behavior

The cockpit prints a short status view and writes a structured result JSON.

It checks:

- raw transcript hygiene,
- `git diff --check`,
- the all-local NotebookLM verifier.

It also reports:

- latest commit,
- tracked raw NotebookLM artifact count,
- NotebookLM test count,
- NotebookLM schema count,
- NotebookLM artifact JSON count.

## Output behavior

By default, cockpit output is written under `/tmp`.

A caller can set:

```bash
export WITT_NOTEBOOKLM_COCKPIT_OUT=/some/path
```

## Authority boundary

A green cockpit does not authorize implementation or provider capture. It only says the local safety/conversion/promotion machinery is coherent.

```text
NotebookLM can inform; local artifacts decide.
```
