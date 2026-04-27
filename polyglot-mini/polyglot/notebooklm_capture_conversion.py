from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .notebooklm_adapter import CONTRACT_VERSION

FIXTURE_SCHEMA_VERSION = 'notebooklm-captured-result-fixture-v0'


def load_notebooklm_captured_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def convert_captured_fixture_to_provider_result(
    fixture: dict[str, Any],
    *,
    run_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if fixture.get('schemaVersion') != FIXTURE_SCHEMA_VERSION:
        raise ValueError('Unsupported NotebookLM captured fixture schema.')
    if fixture.get('provider') != 'notebooklm':
        raise ValueError('Fixture provider must be notebooklm.')

    capture = fixture.get('capture', {})
    fixture_ok = bool(fixture.get('ok'))
    fixture_status = fixture.get('status')
    live_executed = bool(fixture.get('liveNotebookLMExecuted'))
    commands_executed = list(fixture.get('commandsExecuted', []))

    captured = fixture_ok and fixture_status == 'captured_fixture' and not live_executed and commands_executed == []
    errors: list[dict[str, Any]] = []
    if not captured:
        errors.append(
            {
                'code': 'NOTEBOOKLM_CAPTURE_FIXTURE_INVALID',
                'message': 'The NotebookLM captured-result fixture did not satisfy the local captured-fixture boundary.',
                'details': {
                    'fixtureOk': fixture_ok,
                    'fixtureStatus': fixture_status,
                    'liveNotebookLMExecuted': live_executed,
                    'commandsExecuted': commands_executed,
                },
            }
        )

    return {
        'contractVersion': CONTRACT_VERSION,
        'provider': 'notebooklm',
        'status': 'captured' if captured else 'failed',
        'ok': captured,
        'runId': run_id,
        'requestId': request_id,
        'preflight': {
            'source': 'captured_result_fixture',
            'fixtureSchemaVersion': fixture.get('schemaVersion'),
            'liveNotebookLMExecuted': live_executed,
            'commandsExecuted': commands_executed,
        },
        'capture': {
            'mode': 'manual_export',
            'notebookId': None,
            'notebookTitle': 'synthetic captured-result fixture',
            'operation': fixture.get('requestedOperation'),
            'capturedAt': None,
            'rawTextPath': None,
            'metadataPath': capture.get('redactionReportPath'),
            'redactedTextPath': capture.get('redactedTranscriptPath'),
            'fixtureKind': capture.get('kind'),
            'fixtureSource': capture.get('source'),
        },
        'errors': errors,
        'authority': {
            'mayCreateClaims': False,
            'mayAuthorizeImplementation': False,
            'requiresLocalPromotion': True,
            'providerOutputOnly': True,
        },
    }


def provider_result_to_markdown(provider_result: dict[str, Any]) -> str:
    capture = provider_result.get('capture', {})
    authority = provider_result.get('authority', {})
    errors = provider_result.get('errors', [])

    lines = [
        '# NotebookLM provider result',
        '',
        f"- Contract: `{provider_result.get('contractVersion')}`",
        f"- Provider: `{provider_result.get('provider')}`",
        f"- Status: `{provider_result.get('status')}`",
        f"- OK: `{provider_result.get('ok')}`",
        f"- Capture mode: `{capture.get('mode')}`",
        f"- Operation: `{capture.get('operation')}`",
        f"- Raw transcript path: `{capture.get('rawTextPath')}`",
        f"- Redacted transcript path: `{capture.get('redactedTextPath')}`",
        f"- Redaction report path: `{capture.get('metadataPath')}`",
        '',
        '## Authority boundary',
        '',
        f"- May create claims: `{authority.get('mayCreateClaims')}`",
        f"- May authorize implementation: `{authority.get('mayAuthorizeImplementation')}`",
        f"- Requires local promotion: `{authority.get('requiresLocalPromotion')}`",
        '',
    ]
    if errors:
        lines.append('## Errors')
        lines.append('')
        for error in errors:
            lines.append(f"- `{error.get('code')}` {error.get('message')}")
        lines.append('')

    lines.extend(
        [
            '```text',
            'NotebookLM can inform; local artifacts decide.',
            '```',
            '',
        ]
    )
    return '\n'.join(lines)
