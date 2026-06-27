"""Publishers deliver finished Posts to a destination (files, a platform, ...)."""

from __future__ import annotations

from ..config import PublisherConfig
from .base import Publisher
from .markdown import MarkdownPublisher
from .webhook import WebhookPublisher

_REGISTRY: dict[str, type[Publisher]] = {
    "markdown": MarkdownPublisher,
    "webhook": WebhookPublisher,
}


def build_publisher(cfg: PublisherConfig) -> Publisher:
    """Instantiate a Publisher from its config, or raise if the type is unknown."""
    try:
        cls = _REGISTRY[cfg.type]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise ValueError(f"Unknown publisher type {cfg.type!r}. Known types: {known}") from None
    return cls(**cfg.options)


__all__ = ["Publisher", "MarkdownPublisher", "WebhookPublisher", "build_publisher"]
