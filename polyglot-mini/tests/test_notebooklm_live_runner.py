from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from polyglot.notebooklm_live_runner import (
    EXPECTED_GATE,
    EXPECTED_LIVE_ENABLE,
    EXPECTED_READONLY_ENABLE,
    EXPECTED_SUBPROCESS_ENABLE,
    CommandResult,
    evaluate_live_runner_gate,
    run_readonly_list_guarded,
)


class NotebookLMLiveRunnerTests(unittest.TestCase):
    def test_gate_blocks_without_manual_gate(self) -> None:
        gate = evaluate_live_runner_gate({})
        self.assertEqual(gate["status"], "gate_missing")
        self.assertFalse(gate["mayExecute"])

    def test_full_gate_is_required_before_execute(self) -> None:
        env = {
            "WITT_NOTEBOOKLM_MANUAL_GATE": EXPECTED_GATE,
            "WITT_NOTEBOOKLM_ENABLE_READONLY_LIST": EXPECTED_READONLY_ENABLE,
            "WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION": EXPECTED_LIVE_ENABLE,
            "WITT_NOTEBOOKLM_OPERATION": "readonly-list",
            "NOTEBOOKLM_HOME": "/tmp/witt-notebooklm-manual-capture-home",
        }
        gate = evaluate_live_runner_gate(env)
        self.assertEqual(gate["status"], "subprocess_execution_disabled")
        self.assertFalse(gate["mayExecute"])

        env["WITT_NOTEBOOKLM_ALLOW_SUBPROCESS_EXECUTION"] = EXPECTED_SUBPROCESS_ENABLE
        gate = evaluate_live_runner_gate(env)
        self.assertEqual(gate["status"], "ready_to_execute")
        self.assertTrue(gate["mayExecute"])

    def test_guarded_runner_does_not_call_command_runner_when_gate_absent(self) -> None:
        calls = []

        def fake_runner(command, env):
            calls.append((command, env))
            return CommandResult(0, "should not happen", "")

        with tempfile.TemporaryDirectory() as td:
            result = run_readonly_list_guarded(out_root=td, env={}, command_runner=fake_runner)
            self.assertEqual(result["status"], "gate_missing")
            self.assertFalse(result["liveNotebookLMExecuted"])
            self.assertEqual(result["commandsExecuted"], [])
            self.assertEqual(calls, [])
            self.assertTrue((Path(td) / "result.json").exists())

    def test_guarded_runner_can_use_injected_command_runner_and_redacts_output(self) -> None:
        calls = []
        env = {
            "WITT_NOTEBOOKLM_MANUAL_GATE": EXPECTED_GATE,
            "WITT_NOTEBOOKLM_ENABLE_READONLY_LIST": EXPECTED_READONLY_ENABLE,
            "WITT_NOTEBOOKLM_ENABLE_LIVE_EXECUTION": EXPECTED_LIVE_ENABLE,
            "WITT_NOTEBOOKLM_ALLOW_SUBPROCESS_EXECUTION": EXPECTED_SUBPROCESS_ENABLE,
            "WITT_NOTEBOOKLM_OPERATION": "readonly-list",
            "NOTEBOOKLM_HOME": "/tmp/witt-notebooklm-manual-capture-home",
        }

        def fake_runner(command, env_map):
            calls.append((tuple(command), dict(env_map)))
            return CommandResult(
                0,
                "Notebook A\nAuthorization: Bearer fake_secret_token_abcdefghijklmnopqrstuvwxyz123456\n",
                "access_token=fake_access_token_value\n",
            )

        with tempfile.TemporaryDirectory() as td:
            result = run_readonly_list_guarded(out_root=td, env=env, command_runner=fake_runner)
            root = Path(td)
            self.assertEqual(result["status"], "readonly_probe_captured")
            self.assertTrue(result["ok"])
            self.assertTrue(result["liveNotebookLMExecuted"])
            self.assertEqual(result["commandsExecuted"], ["notebooklm list"])
            self.assertEqual(calls[0][0], ("notebooklm", "list"))

            redacted_stdout = (root / "transcript.stdout.redacted.txt").read_text()
            redacted_stderr = (root / "transcript.stderr.redacted.txt").read_text()
            self.assertIn("Notebook A", redacted_stdout)
            self.assertNotIn("fake_secret_token", redacted_stdout)
            self.assertNotIn("fake_access_token_value", redacted_stderr)
            stdout_report = json.loads((root / "redaction-report.stdout.json").read_text())
            stderr_report = json.loads((root / "redaction-report.stderr.json").read_text())
            self.assertGreaterEqual(stdout_report["totalRedactions"], 1)
            self.assertGreaterEqual(stderr_report["totalRedactions"], 1)


if __name__ == "__main__":
    unittest.main()
