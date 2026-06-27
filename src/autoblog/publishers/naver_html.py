"""Deterministic Markdown -> Naver-style inline-styled HTML.

Naver's SmartEditor strips external CSS, so every element carries an inline
``style``. Headings render at ``heading_px`` (default 22), body text at
``body_px`` (default 18), with generous spacing for readability. Image markers
(``![alt](IMAGE)``) become visible placeholders for the human to fill in.

This is a small, intentional subset of Markdown (headings, paragraphs, bullet
lists, bold, links, image placeholders) — the generator is instructed to emit
only that subset, and keeping the renderer deterministic makes it unit-testable.
"""

from __future__ import annotations

import html
import re

_IMAGE_RE = re.compile(r"^!\[(?P<alt>.*?)\]\((?P<url>.*?)\)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def markdown_to_naver_html(body_md: str, *, heading_px: int = 22, body_px: int = 18) -> str:
    """Render a Markdown body to a Naver-paste-ready HTML fragment."""
    heading_style = f"font-size:{heading_px}px; font-weight:bold; margin:24px 0 12px;"
    para_style = f"font-size:{body_px}px; line-height:1.8; margin:0 0 16px;"
    li_style = f"font-size:{body_px}px; line-height:1.8; margin:0 0 8px;"
    placeholder_style = (
        f"font-size:{body_px}px; color:#888888; border:1px dashed #cccccc; "
        "padding:12px; text-align:center; margin:0 0 16px;"
    )

    parts: list[str] = []
    for block in _split_blocks(body_md):
        lines = block.splitlines()

        if len(lines) == 1 and (m := _IMAGE_RE.match(lines[0].strip())):
            alt = _inline(m.group("alt"))
            parts.append(f'<p style="{placeholder_style}">[이미지 자리: {alt}]</p>')
            continue

        if lines[0].lstrip().startswith("#"):
            text = _inline(lines[0].lstrip("#").strip())
            parts.append(f'<h3 style="{heading_style}">{text}</h3>')
            continue

        if all(line.lstrip().startswith("- ") for line in lines):
            items = "".join(
                f'<li style="{li_style}">{_inline(line.lstrip()[2:].strip())}</li>'
                for line in lines
            )
            parts.append(f'<ul style="margin:0 0 16px; padding-left:24px;">{items}</ul>')
            continue

        joined = "<br>".join(_inline(line.strip()) for line in lines)
        parts.append(f'<p style="{para_style}">{joined}</p>')

    return "\n".join(parts)


def _split_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _inline(text: str) -> str:
    """Escape HTML, then apply links and bold. Order matters: escape first."""
    escaped = html.escape(text, quote=False)
    escaped = _LINK_RE.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        escaped,
    )
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    return escaped
