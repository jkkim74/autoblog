"""Generators turn source material into finished Posts."""

from __future__ import annotations

from ..config import BlogConfig, GeneratorConfig
from .base import Generator
from .claude import ClaudeGenerator

_REGISTRY: dict[str, type[Generator]] = {
    "claude": ClaudeGenerator,
}


def build_generator(cfg: GeneratorConfig, blog: BlogConfig) -> Generator:
    """Instantiate a Generator from its config, or raise if the type is unknown."""
    try:
        cls = _REGISTRY[cfg.type]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise ValueError(f"Unknown generator type {cfg.type!r}. Known types: {known}") from None
    return cls(cfg, blog)


__all__ = ["Generator", "ClaudeGenerator", "build_generator"]
