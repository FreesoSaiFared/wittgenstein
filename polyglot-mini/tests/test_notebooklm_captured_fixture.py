from __future__ import annotations

import json
import unittest
from pathlib import Path


class NotebookLMCapturedFixtureTests(unittest.TestCase):
    def fixture_root(self) -> Path:
        return Path(__file__).resolve().parents[2] / "artifacts" / "manual-gated" / "notebooklm" / "captured-result-fixture"

    def test_fixture_contains_no_live_execution_and_no_authority(self) -> None:
        root = self.fixture_root()
        result = json.loads((root / "result.json").read_text())

        self.assertEqual(result["schemaVersion"], "notebooklm-captured-result-fixture-v0")
        self.assertEqual(result["provider"], "notebooklm")
        self.assertEqual(result["status"], "captured_fixture")
        self.assertFalse(result["liveNotebookLMExecuted"])
        self.assertEqual(result["commandsExecuted"], [])
        self.assertFalse(result["authority"]["mayCreateClaims"])
        self.assertFalse(result["authority"]["mayAuthorizeImplementation"])
        self.assertTrue(result["authority"]["requiresLocalPromotion"])

    def test_fixture_uses_redacted_transcript_only(self) -> None:
        root = self.fixture_root()
        result = json.loads((root / "result.json").read_text())
        transcript_path = Path(result["capture"]["redactedTranscriptPath"])
        report_path = Path(result["capture"]["redactionReportPath"])

        self.assertTrue(transcript_path.exists())
        self.assertTrue(report_path.exists())
        self.assertFalse((root / "transcript.stdout.raw.txt").exists())

        transcript = transcript_path.read_text()
        self.assertIn("Synthetic Research Notebook", transcript)
        self.assertNotIn("Bearer ", transcript)
        self.assertNotIn("access_token", transcript)

        report = json.loads(report_path.read_text())
        self.assertEqual(report["schemaVersion"], "notebooklm-redaction-report-v0")
        self.assertFalse(report["liveNotebookLMExecuted"])


if __name__ == "__main__":
    unittest.main()
