from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class NotebookLMPromotionDecisionPathsTests(unittest.TestCase):
    def root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def script(self) -> Path:
        return self.root() / "scripts" / "list_notebooklm_promotion_decisions.sh"

    def test_text_output_lists_rendered_decision_paths(self) -> None:
        completed = subprocess.run(
            [str(self.script())],
            cwd=self.root(),
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("NotebookLM rendered promotion decisions", completed.stdout)
        self.assertIn("executor-context-block-decision.md", completed.stdout)
        self.assertIn("patch-authority-block-decision.md", completed.stdout)

    def test_json_output_preserves_no_authority_boundary(self) -> None:
        completed = subprocess.run(
            [str(self.script()), "--json"],
            cwd=self.root(),
            text=True,
            capture_output=True,
            check=True,
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["schemaVersion"], "notebooklm-promotion-decision-paths-v0")
        self.assertEqual(result["provider"], "notebooklm")
        self.assertEqual(result["mode"], "promotion_decision_paths")
        self.assertTrue(result["ok"])
        self.assertFalse(result["liveNotebookLMExecuted"])
        self.assertEqual(result["commandsExecuted"], [])
        self.assertFalse(result["authority"]["mayCreateClaims"])
        self.assertFalse(result["authority"]["mayAuthorizeImplementation"])
        self.assertGreaterEqual(result["count"], 2)
        self.assertTrue(any(path.endswith("executor-context-block-decision.md") for path in result["paths"]))
        self.assertTrue(any(path.endswith("patch-authority-block-decision.md") for path in result["paths"]))

    def test_bad_argument_fails_with_usage(self) -> None:
        completed = subprocess.run(
            [str(self.script()), "--bogus"],
            cwd=self.root(),
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("usage:", completed.stderr)


if __name__ == "__main__":
    unittest.main()
