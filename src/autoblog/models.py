"""Core data structures passed between sources, generators, and publishers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class SourceItem:
    """A single piece of raw material pulled from a source (e.g. an RSS entry)."""

    title: str
    url: str
    summary: str = ""
    source_name: str = ""
    published: datetime | None = None


@dataclass(slots=True)
class Post:
    """A generated blog post, ready to be published."""

    title: str
    body: str
    slug: str
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Provenance: the source items this post was generated from.
    sources: list[SourceItem] = field(default_factory=list)
