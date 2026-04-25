#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "polyglot-mini"))

from polyglot.notebooklm_promotion_render import render_promotion_decision_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a NotebookLM promotion decision JSON file as Markdown.")
    parser.add_argument("--input", required=True, help="Promotion decision JSON path")
    parser.add_argument("--output", required=True, help="Markdown output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    decision = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_promotion_decision_markdown(decision), encoding="utf-8")
    print(f"rendered={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
