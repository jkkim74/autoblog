"""Write posts as Markdown files with YAML front matter.

The output format is compatible with common static site generators (Hugo,
Jekyll, Eleventy): a `---` front-matter block followed by the Markdown body.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import Post
from .base import Publisher


class MarkdownPublisher(Publisher):
    def __init__(self, output_dir: str = "content/posts") -> None:
        self.output_dir = Path(output_dir)

    def publish(self, post: Post) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        date = post.created_at.strftime("%Y-%m-%d")
        path = self.output_dir / f"{date}-{post.slug}.md"

        front_matter = {
            "title": post.title,
            "date": post.created_at.isoformat(),
            "summary": post.summary,
            "tags": post.tags,
            "sources": [{"title": s.title, "url": s.url} for s in post.sources],
        }
        # default_flow_style=False keeps lists/maps block-styled and readable.
        fm = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True).strip()
        path.write_text(f"---\n{fm}\n---\n\n{post.body}\n", encoding="utf-8")
        return str(path)
