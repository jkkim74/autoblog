"""RSS/Atom source backed by feedparser.

Fetching goes through httpx so we get a real timeout and surface HTTP errors;
feedparser only parses the bytes. feedparser never raises, so malformed feeds
are reported via ``parsed.bozo`` rather than swallowed silently.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import struct_time

import feedparser
import httpx

from ..models import SourceItem
from .base import Source

log = logging.getLogger("autoblog")


class RSSSource(Source):
    """Pull entries from an RSS or Atom feed."""

    def __init__(self, name: str, url: str, max_items: int = 5, timeout: float = 15.0) -> None:
        super().__init__(name)
        self.url = url
        self.max_items = max_items
        self.timeout = timeout

    def fetch(self) -> list[SourceItem]:
        try:
            resp = httpx.get(self.url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("RSS source %r could not fetch %s: %s", self.name, self.url, exc)
            return []

        parsed = feedparser.parse(resp.content)
        if parsed.bozo:
            log.warning(
                "RSS source %r returned a malformed feed: %s",
                self.name,
                parsed.get("bozo_exception"),
            )

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
