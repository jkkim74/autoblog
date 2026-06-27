"""Deterministic content checks that feed the human-review notes.

These are cheap regex scans (no LLM): they flag hype/over-promise phrasing that
is risky for a Korean blog (guaranteed-income claims, absolutes, etc.) so a
human reviewer sees them before publishing. The model's own review warnings are
merged with these.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Default Korean over-promise / hype expressions. Override via config.
DEFAULT_FORBIDDEN: tuple[str, ...] = (
    "무조건",
    "100%",
    "100 %",
    "확정 수익",
    "수익 보장",
    "보장",
    "절대",
    "최고",
    "유일",
    "완벽",
)


def scan_forbidden(text: str, patterns: Iterable[str] = DEFAULT_FORBIDDEN) -> list[str]:
    """Return one warning per forbidden expression found in ``text``.

    Matching is case-insensitive and substring-based (after escaping), which is
    appropriate for the short fixed phrases above.
    """
    warnings: list[str] = []
    for pattern in patterns:
        if re.search(re.escape(pattern), text, flags=re.IGNORECASE):
            warnings.append(f"과장/금지 표현 감지: '{pattern}'")
    return warnings
