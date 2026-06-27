"""Persistent record of which source items have already been turned into posts.

Keyed by ``SourceItem.url`` so repeated or scheduled (cron) runs skip content
they have already published instead of regenerating duplicate posts.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

log = logging.getLogger("autoblog")


class SeenStore:
    """A tiny JSON-backed set of already-seen item URLs."""

    def __init__(self, path: str | Path = ".autoblog-state.json") -> None:
        self.path = Path(path)
        self._seen: set[str] = self._load()

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning("Could not read state file %s; starting fresh.", self.path)
            return set()
        return set(data.get("seen", []))

    def is_seen(self, url: str) -> bool:
        # Empty URLs can't be deduplicated reliably, so treat them as always new.
        return bool(url) and url in self._seen

    def add(self, urls: Iterable[str]) -> None:
        self._seen.update(u for u in urls if u)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen": sorted(self._seen)}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
