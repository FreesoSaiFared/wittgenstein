# NotebookLM Install Probe Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a reproducible local probe for `notebooklm-py` installation and local metadata detection without wiring real NotebookLM into Wittgenstein.

**Architecture:** Keep the probe outside dossier-core. Recreate an isolated venv under `/tmp`, install `notebooklm-py`, capture only local package/import/CLI facts, and record the verified contract in docs. Add a small helper script so the lane can be rerun without guessing commands.

**Tech Stack:** bash, Python venv, pip, importlib.metadata, unittest

---

### Task 1: Add the probe helper

**Files:**
- Create: `scripts/notebooklm_py_install_probe.sh`
- Document: `docs/contracts/notebooklm-py-install-probe.md`

1. Create a shell helper that recreates `/tmp/witt-notebooklm-py-probe-venv`.
2. Install `notebooklm-py` with `python -m pip install notebooklm-py`.
3. Record python version, `pip show`, import probes, distribution metadata, entry points, `command -v`, and CLI `--help` if present.
4. Persist the raw probe report to `/tmp/witt-notebooklm-py-probe-report.txt`.

### Task 2: Update contract/status docs

**Files:**
- Create: `docs/progress/notebooklm-install-probe-status.md`
- Modify: `docs/contracts/notebooklm-py-invocation-contract.md`

1. Convert the old “ABSENT everywhere” contract into the narrower, verified isolated-venv contract.
2. Keep the verdict explicit about what is still unverified: auth, browser login, real NotebookLM calls, and dossier integration.

### Task 3: Verification

**Files:**
- Test: `polyglot-mini/tests/test_dossier.py`

1. Run `PYTHONPATH=polyglot-mini python3 -m unittest -v polyglot-mini/tests/test_dossier.py`.
2. Review output before claiming completion.
3. Commit only docs/probe-helper changes; do not commit `/tmp` artifacts.
