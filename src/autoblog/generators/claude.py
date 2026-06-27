"""Claude-backed generator: rewrites source material into an original post.

Uses the Anthropic Messages API with adaptive thinking, the effort parameter,
streaming (so large drafts don't hit HTTP timeouts), and structured outputs so
the response is guaranteed-parseable JSON.
"""

from __future__ import annotations

import json

from slugify import slugify

from ..config import BlogConfig, GeneratorConfig
from ..models import Post, SourceItem
from .base import Generator
from .client import build_client, resolve_model_id

# Structured-output schema. With output_config.format the model is constrained
# to emit exactly this shape, so json.loads on the final text block is safe.
_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "body": {"type": "string", "description": "The post body in Markdown."},
    },
    "required": ["title", "summary", "tags", "body"],
    "additionalProperties": False,
}


class ClaudeGenerator(Generator):
    def __init__(self, cfg: GeneratorConfig, blog: BlogConfig) -> None:
        self.cfg = cfg
        self.blog = blog
        self.client = build_client(cfg)
        self.model_id = resolve_model_id(cfg)

    def generate(self, items: list[SourceItem]) -> Post:
        if not items:
            raise ValueError("ClaudeGenerator.generate requires at least one source item.")

        system = (
            f"You are the writer for a blog titled {self.blog.title!r}. "
            "You are given source material (titles, links, summaries) and must write "
            "ONE original blog post that synthesizes it. Do not copy text verbatim; "
            "write something new and useful. Attribute facts to their sources by linking. "
            f"Style guidance: {self.blog.style.strip()} "
            f"Aim for about {self.blog.target_words} words."
        )

        with self.client.messages.stream(
            model=self.model_id,
            max_tokens=16000,
            system=system,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.cfg.effort,
                "format": {"type": "json_schema", "schema": _POST_SCHEMA},
            },
            messages=[{"role": "user", "content": _render_prompt(items)}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            raise RuntimeError("Claude refused to generate this post (safety stop).")
        if message.stop_reason == "max_tokens":
            raise RuntimeError(
                "Generation hit the max_tokens limit, so the JSON output is truncated. "
                "Lower 'target_words' or raise max_tokens in ClaudeGenerator."
            )

        text = next((b.text for b in message.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Claude returned output that is not valid JSON (stop_reason="
                f"{message.stop_reason!r}): {exc}"
            ) from exc

        return Post(
            title=data["title"],
            body=data["body"],
            slug=slugify(data["title"])[:80] or "post",
            tags=list(data.get("tags", [])),
            summary=data.get("summary", ""),
            sources=items,
        )


def _render_prompt(items: list[SourceItem]) -> str:
    lines = ["Source material:\n"]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item.title}")
        lines.append(f"   Link: {item.url}")
        if item.summary:
            lines.append(f"   Summary: {item.summary}")
        lines.append("")
    lines.append(
        "Write the post now. Return JSON matching the requested schema. "
        "The body must be Markdown and should link to the source URLs where relevant."
    )
    return "\n".join(lines)
