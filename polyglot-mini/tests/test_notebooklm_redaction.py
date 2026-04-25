from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from polyglot.notebooklm_redaction import REPORT_SCHEMA_VERSION, redact_text


class NotebookLMRedactionTests(unittest.TestCase):
    def test_redacts_common_secret_shapes(self) -> None:
        secret_blob = (
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890\n"
            "Cookie: SID=secret_sid_value; __Secure-1PSID=secret_secure_cookie; theme=ok\n"
            "access_token=ya29.this_should_not_survive\n"
            "https://example.invalid/callback?code=oauth-code-value&x=1\n"
            "opaque ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 more\n"
            "normal line survives\n"
        )

        redacted, report = redact_text(secret_blob)

        self.assertEqual(report["schemaVersion"], REPORT_SCHEMA_VERSION)
        self.assertTrue(report["changed"])
        self.assertGreaterEqual(report["totalRedactions"], 5)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz1234567890", redacted)
        self.assertNotIn("secret_sid_value", redacted)
        self.assertNotIn("secret_secure_cookie", redacted)
        self.assertNotIn("ya29.this_should_not_survive", redacted)
        self.assertNotIn("oauth-code-value", redacted)
        self.assertIn("normal line survives", redacted)
        self.assertFalse(report["liveNotebookLMExecuted"])
        self.assertFalse(report["authority"]["mayAuthorizeImplementation"])

    def test_redaction_is_stable_when_no_secret_present(self) -> None:
        text = "NotebookLM can inform; local artifacts decide.\n"
        redacted, report = redact_text(text)
        self.assertEqual(redacted, text)
        self.assertFalse(report["changed"])
        self.assertEqual(report["totalRedactions"], 0)

    def test_cli_writes_redacted_output_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.txt"
            output_path = root / "redacted.txt"
            report_path = root / "report.json"
            input_path.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")

            repo_root = Path(__file__).resolve().parents[2]
            script = repo_root / "scripts" / "notebooklm_redact_transcript.py"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root / "polyglot-mini")
            completed = subprocess.run(
                [sys.executable, str(script), "--input", str(input_path), "--output", str(output_path), "--report", str(report_path)],
                check=True,
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertIn("redacted=", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertTrue(report_path.exists())
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", output_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(report["totalRedactions"], 1)


if __name__ == "__main__":
    unittest.main()
