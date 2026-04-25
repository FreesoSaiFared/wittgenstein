#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "polyglot-mini"))

from polyglot.notebooklm_redaction import redact_text  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact NotebookLM transcript text before storing it as provider evidence.")
    parser.add_argument("--input", required=True, help="Input transcript path")
    parser.add_argument("--output", required=True, help="Redacted transcript output path")
    parser.add_argument("--report", required=True, help="Redaction report JSON path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report)

    text = input_path.read_text(encoding="utf-8")
    redacted, report = redact_text(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(redacted, encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"redacted={report['totalRedactions']} changed={str(report['changed']).lower()} output={output_path} report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
