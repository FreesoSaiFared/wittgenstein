#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "polyglot-mini"))

from polyglot.notebooklm_live_runner import run_readonly_list_guarded  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded NotebookLM readonly-list runner.")
    parser.add_argument("--out", default="artifacts/manual-gated/notebooklm/live-runner-guarded-dry-run")
    args = parser.parse_args()

    result = run_readonly_list_guarded(out_root=args.out)
    print(json.dumps({
        "status": result["status"],
        "ok": result["ok"],
        "liveNotebookLMExecuted": result["liveNotebookLMExecuted"],
        "commandsExecuted": result["commandsExecuted"],
        "resultPath": str(Path(args.out) / "result.json"),
    }, indent=2, sort_keys=True))

    if result["status"] in {"gate_missing", "home_missing", "readonly_enable_missing", "blocked"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
