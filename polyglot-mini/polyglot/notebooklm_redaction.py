from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

REPORT_SCHEMA_VERSION = "notebooklm-redaction-report-v0"
REDACTION_TOKEN = "[REDACTED]"


@dataclass(frozen=True)
class RedactionRule:
    name: str
    pattern: re.Pattern[str]
    replacement: str | None = None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


RULES: tuple[RedactionRule, ...] = (
    RedactionRule(
        "HTTP_AUTHORIZATION_BEARER",
        re.compile(r"(?im)^(\s*authorization\s*:\s*bearer\s+)([^\s]+)"),
        r"\1[REDACTED_BEARER_TOKEN]",
    ),
    RedactionRule(
        "COOKIE_HEADER",
        re.compile(r"(?im)^(\s*(?:cookie|set-cookie)\s*:\s*).+$"),
        r"\1[REDACTED_COOKIE_HEADER]",
    ),
    RedactionRule(
        "JSON_OR_ENV_TOKEN_FIELD",
        re.compile(
            r"(?i)(\b(?:access_token|refresh_token|id_token|csrf_token|xsrf_token|session_id|sessionid|sid|hsid|ssid|sapisid|apisid|authorization|auth_token|oauth_token)\b\s*[=:]\s*['\"]?)([^'\"\s,;}{]+)(['\"]?)"
        ),
        r"\1[REDACTED_TOKEN]\3",
    ),
    RedactionRule(
        "URL_SECRET_PARAMETER",
        re.compile(
            r"(?i)([?&](?:access_token|refresh_token|id_token|csrf_token|xsrf_token|session|session_id|sid|token|code)=)([^&\s]+)"
        ),
        r"\1[REDACTED_URL_SECRET]",
    ),
    RedactionRule(
        "GOOGLE_SECURE_COOKIE_NAME",
        re.compile(
            r"(?i)\b((?:__Secure-[A-Za-z0-9_\-]+|SID|HSID|SSID|APISID|SAPISID|LOGIN_INFO)\s*=\s*)([^;\s]+)"
        ),
        r"\1[REDACTED_COOKIE_VALUE]",
    ),
    RedactionRule(
        "LONG_OPAQUE_SECRET_LIKE_STRING",
        re.compile(r"(?<![A-Za-z0-9_\-])([A-Za-z0-9_\-\.=]{48,})(?![A-Za-z0-9_\-])"),
        "[REDACTED_OPAQUE_STRING]",
    ),
)


def redact_text(text: str, *, rules: Iterable[RedactionRule] = RULES) -> tuple[str, dict]:
    redacted = text
    entries: list[dict] = []

    for rule in rules:
        replacement = rule.replacement if rule.replacement is not None else REDACTION_TOKEN
        redacted, count = rule.pattern.subn(replacement, redacted)
        if count:
            entries.append({"type": rule.name, "count": count})

    report = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "inputSha256": sha256_text(text),
        "outputSha256": sha256_text(redacted),
        "changed": redacted != text,
        "totalRedactions": sum(entry["count"] for entry in entries),
        "redactions": entries,
        "liveNotebookLMExecuted": False,
        "authority": {
            "mayCreateClaims": False,
            "mayAuthorizeImplementation": False,
            "requiresLocalPromotion": True,
            "providerOutputOnly": True,
        },
    }
    return redacted, report
