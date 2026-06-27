from datetime import datetime, timezone

import yaml

from autoblog.models import Post, SourceItem
from autoblog.publishers.markdown import MarkdownPublisher


def test_markdown_publish_writes_front_matter(tmp_path):
    post = Post(
        title="Hello World",
        body="# Heading\n\nSome body text.",
        slug="hello-world",
        tags=["a", "b"],
        summary="A short summary.",
        created_at=datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc),
        sources=[SourceItem(title="Src", url="https://example.com")],
    )
    publisher = MarkdownPublisher(output_dir=str(tmp_path))
    location = publisher.publish(post)

    assert location.endswith("2026-06-27-hello-world.md")
    text = (tmp_path / "2026-06-27-hello-world.md").read_text(encoding="utf-8")

    front, _, body = text.partition("\n---\n")
    meta = yaml.safe_load(front.removeprefix("---\n"))
    assert meta["title"] == "Hello World"
    assert meta["tags"] == ["a", "b"]
    assert meta["sources"][0]["url"] == "https://example.com"
    assert "Some body text." in body
