"""Sources pull raw material (SourceItems) that generators turn into posts."""

from __future__ import annotations

from ..config import SourceConfig
from .base import Source
from .rss import RSSSource

_REGISTRY: dict[str, type[Source]] = {
    "rss": RSSSource,
}


def build_source(cfg: SourceConfig) -> Source:
    """Instantiate a Source from its config, or raise if the type is unknown."""
    try:
        cls = _REGISTRY[cfg.type]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise ValueError(f"Unknown source type {cfg.type!r}. Known types: {known}") from None
    return cls(name=cfg.name, **cfg.options)


__all__ = ["Source", "RSSSource", "build_source"]
