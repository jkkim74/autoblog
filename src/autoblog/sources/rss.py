"""RSS/Atom source backed by feedparser."""

from __future__ import annotations

from datetime import datetime, timezone
from time import struct_time

import feedparser

from ..models import SourceItem
from .base import Source


class RSSSource(Source):
    """Pull entries from an RSS or Atom feed."""

    def __init__(self, name: str, url: str, max_items: int = 5) -> None:
        super().__init__(name)
        self.url = url
        self.max_items = max_items

    def fetch(self) -> list[SourceItem]:
        parsed = feedparser.parse(self.url)
        items: list[SourceItem] = []
        for entry in parsed.entries[: self.max_items]:
            items.append(
                SourceItem(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", "").strip(),
                    summary=entry.get("summary", "").strip(),
                    source_name=self.name,
                    published=_to_datetime(entry.get("published_parsed")),
                )
            )
        return items


def _to_datetime(value: struct_time | None) -> datetime | None:
    if value is None:
        return None
    return datetime(*value[:6], tzinfo=timezone.utc)
