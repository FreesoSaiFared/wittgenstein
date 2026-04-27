# NotebookLM Captured Result Fixture Contract

Date: 2026-04-25  
Status: synthetic local fixture, no live NotebookLM operation  
Provider: `notebooklm`

## Purpose

This contract defines a local captured-result fixture for the future `readonly-list` NotebookLM probe.

The fixture lets the repository test the result shape without touching NotebookLM.

## Non-goal

This fixture does not:

- run NotebookLM,
- prove auth works,
- list real notebooks,
- upload or mutate sources,
- create implementation authority,
- create patch authority.

## Fixture status

The fixture status is:

```text
captured_fixture
```

This means the capture shape is tested locally. It does not mean a live provider capture has occurred.

## Authority boundary

A captured fixture is provider evidence only.

```text
NotebookLM can inform; local artifacts decide.
```
