from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from polyglot.notebooklm_promotion_render import render_promotion_decision_markdown


class NotebookLMPromotionRenderTests(unittest.TestCase):
    def root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def decision_path(self) -> Path:
        return self.root() / "artifacts" / "manual-gated" / "notebooklm" / "promotion-blocking-fixture" / "executor-context-block-decision.json"

    def test_renderer_preserves_boundary_and_errors(self) -> None:
        decision = json.loads(self.decision_path().read_text())
        markdown = render_promotion_decision_markdown(decision)

        self.assertIn("# NotebookLM promotion decision", markdown)
        self.assertIn("Can enter executor context: `False`", markdown)
        self.assertIn("Can authorize patch: `False`", markdown)
        self.assertIn("NOTEBOOKLM_LOCAL_PROMOTION_REQUIRED", markdown)
        self.assertIn("NotebookLM can inform; local artifacts decide.", markdown)

    def test_cli_renders_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "decision.md"
            script = self.root() / "scripts" / "render_notebooklm_promotion_decision.py"
            completed = subprocess.run(
                [sys.executable, str(script), "--input", str(self.decision_path()), "--output", str(out)],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("rendered=", completed.stdout)
            text = out.read_text()
            self.assertIn("# NotebookLM promotion decision", text)
            self.assertIn("Can authorize patch: `False`", text)


if __name__ == "__main__":
    unittest.main()
