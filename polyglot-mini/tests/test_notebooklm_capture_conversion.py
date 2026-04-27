from __future__ import annotations

import json
import unittest
from pathlib import Path

from polyglot.notebooklm_capture_conversion import (
    convert_captured_fixture_to_provider_result,
    load_notebooklm_captured_fixture,
    provider_result_to_markdown,
)


class NotebookLMCaptureConversionTests(unittest.TestCase):
    def fixture_root(self) -> Path:
        return Path(__file__).resolve().parents[2] / 'artifacts' / 'manual-gated' / 'notebooklm' / 'captured-result-fixture'

    def test_fixture_converts_to_provider_result_without_authority(self) -> None:
        fixture = load_notebooklm_captured_fixture(self.fixture_root() / 'result.json')
        result = convert_captured_fixture_to_provider_result(fixture, run_id='fixture-run', request_id='fixture-request')

        self.assertEqual(result['contractVersion'], 'notebooklm-provider-result-v0')
        self.assertEqual(result['provider'], 'notebooklm')
        self.assertEqual(result['status'], 'captured')
        self.assertTrue(result['ok'])
        self.assertEqual(result['runId'], 'fixture-run')
        self.assertEqual(result['requestId'], 'fixture-request')
        self.assertEqual(result['capture']['mode'], 'manual_export')
        self.assertEqual(result['capture']['operation'], 'readonly-list')
        self.assertIsNone(result['capture']['rawTextPath'])
        self.assertIn('transcript.stdout.redacted.txt', result['capture']['redactedTextPath'])
        self.assertFalse(result['authority']['mayCreateClaims'])
        self.assertFalse(result['authority']['mayAuthorizeImplementation'])
        self.assertTrue(result['authority']['requiresLocalPromotion'])
        self.assertEqual(result['errors'], [])

    def test_invalid_fixture_fails_closed(self) -> None:
        fixture = load_notebooklm_captured_fixture(self.fixture_root() / 'result.json')
        fixture['liveNotebookLMExecuted'] = True

        result = convert_captured_fixture_to_provider_result(fixture)

        self.assertFalse(result['ok'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['errors'][0]['code'], 'NOTEBOOKLM_CAPTURE_FIXTURE_INVALID')
        self.assertFalse(result['authority']['mayAuthorizeImplementation'])

    def test_provider_result_markdown_preserves_boundary(self) -> None:
        fixture = load_notebooklm_captured_fixture(self.fixture_root() / 'result.json')
        result = convert_captured_fixture_to_provider_result(fixture)
        markdown = provider_result_to_markdown(result)

        self.assertIn('Status: `captured`', markdown)
        self.assertIn('Capture mode: `manual_export`', markdown)
        self.assertIn('May authorize implementation: `False`', markdown)
        self.assertIn('NotebookLM can inform; local artifacts decide.', markdown)
        self.assertNotIn('Bearer ', markdown)

    def test_generated_conversion_artifact_is_valid_json(self) -> None:
        root = Path(__file__).resolve().parents[2] / 'artifacts' / 'manual-gated' / 'notebooklm' / 'provider-result-conversion-fixture'
        result_path = root / 'provider-result.json'
        if result_path.exists():
            result = json.loads(result_path.read_text())
            self.assertEqual(result['contractVersion'], 'notebooklm-provider-result-v0')
            self.assertEqual(result['status'], 'captured')


if __name__ == '__main__':
    unittest.main()
