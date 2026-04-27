from __future__ import annotations

import unittest
from pathlib import Path


class NotebookLMPromotionRendererStatusWireTests(unittest.TestCase):
    def root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_cockpit_reports_rendered_promotion_decision_docs_without_running_it(self) -> None:
        cockpit = (self.root() / "scripts" / "notebooklm_status_cockpit.sh").read_text()

        self.assertIn("promotionDecisionMarkdownCount", cockpit)
        self.assertIn("promotionDecisionMarkdownPaths", cockpit)
        self.assertIn("Rendered promotion decision docs", cockpit)
        self.assertIn("promotion-decision-renderer", cockpit)

    def test_status_docs_point_to_rendered_decisions(self) -> None:
        current = (self.root() / "docs" / "status" / "notebooklm-provider-current-state.md").read_text()
        lane_index = (self.root() / "docs" / "status" / "notebooklm-lane-index.md").read_text()

        self.assertIn("## Readable promotion decisions", current)
        self.assertIn("executor-context-block-decision.md", current)
        self.assertIn("patch-authority-block-decision.md", current)
        self.assertIn("Promotion decision renderer", lane_index)

    def test_rendered_decision_fixtures_exist(self) -> None:
        base = self.root() / "artifacts" / "manual-gated" / "notebooklm" / "promotion-decision-renderer"
        executor = base / "executor-context-block-decision.md"
        patch = base / "patch-authority-block-decision.md"

        self.assertTrue(executor.exists())
        self.assertTrue(patch.exists())
        self.assertIn("Can authorize patch: `False`", executor.read_text())
        self.assertIn("Can authorize patch: `False`", patch.read_text())


if __name__ == "__main__":
    unittest.main()
