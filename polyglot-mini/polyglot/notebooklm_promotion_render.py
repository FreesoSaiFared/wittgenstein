from __future__ import annotations

from typing import Any


def render_promotion_decision_markdown(decision: dict[str, Any]) -> str:
    authority = decision.get("authority", {})
    validation = decision.get("localPromotionValidation")
    errors = decision.get("errors", [])

    lines = [
        "# NotebookLM promotion decision",
        "",
        f"- Provider: `{decision.get('provider')}`",
        f"- Target: `{decision.get('target')}`",
        f"- OK: `{decision.get('ok')}`",
        f"- Can enter executor context: `{decision.get('canEnterExecutorContext')}`",
        f"- Can authorize patch: `{decision.get('canAuthorizePatch')}`",
        f"- Requires local promotion: `{decision.get('requiresLocalPromotion')}`",
        f"- Provider result status: `{decision.get('providerResultStatus')}`",
        "",
        "## Authority boundary",
        "",
        f"- Provider may create claims: `{authority.get('providerMayCreateClaims')}`",
        f"- Provider may authorize implementation: `{authority.get('providerMayAuthorizeImplementation')}`",
        f"- Local promotion required: `{authority.get('localPromotionRequired')}`",
        "",
    ]

    if validation is not None:
        lines.extend(
            [
                "## Local promotion validation",
                "",
                f"- Validation OK: `{validation.get('ok')}`",
                f"- Allowed targets: `{', '.join(validation.get('allowedTargets', []))}`",
                f"- Allows patch authority: `{validation.get('allowsPatchAuthority')}`",
                "",
            ]
        )
        validation_errors = validation.get("errors", [])
        if validation_errors:
            lines.extend(["### Validation errors", ""])
            for error in validation_errors:
                lines.append(f"- `{error.get('code')}` {error.get('message')}")
            lines.append("")

    if errors:
        lines.extend(["## Decision errors", ""])
        for error in errors:
            lines.append(f"- `{error.get('code')}` {error.get('message')}")
        lines.append("")

    lines.extend(
        [
            "```text",
            "NotebookLM can inform; local artifacts decide.",
            "```",
            "",
        ]
    )
    return "\n".join(lines)
