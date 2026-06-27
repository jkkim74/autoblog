"""Load and validate the YAML config into typed dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when the config file is missing required fields or malformed."""


@dataclass(slots=True)
class BlogConfig:
    title: str = "My Auto Blog"
    style: str = ""
    target_words: int = 700


@dataclass(slots=True)
class GeneratorConfig:
    type: str = "claude"
    model: str = "claude-opus-4-8"
    effort: str = "high"


@dataclass(slots=True)
class SourceConfig:
    type: str
    name: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PublisherConfig:
    type: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Config:
    blog: BlogConfig
    generator: GeneratorConfig
    sources: list[SourceConfig]
    publishers: list[PublisherConfig]


def load_config(path: str | Path) -> Config:
    """Parse a YAML config file into a Config. Raises ConfigError on problems."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("Top-level config must be a mapping.")

    blog = BlogConfig(**_subdict(raw.get("blog", {}), BlogConfig))
    generator = GeneratorConfig(**_subdict(raw.get("generator", {}), GeneratorConfig))

    sources = [_parse_source(s) for s in raw.get("sources", [])]
    if not sources:
        raise ConfigError("At least one source is required under 'sources'.")

    publishers = [_parse_publisher(p) for p in raw.get("publishers", [])]
    if not publishers:
        raise ConfigError("At least one publisher is required under 'publishers'.")

    return Config(blog=blog, generator=generator, sources=sources, publishers=publishers)


def _subdict(data: dict[str, Any], cls: type) -> dict[str, Any]:
    """Keep only keys that are fields on the dataclass, so unknown keys don't crash."""
    allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
    return {k: v for k, v in data.items() if k in allowed}


def _parse_source(data: dict[str, Any]) -> SourceConfig:
    if "type" not in data:
        raise ConfigError("Each source needs a 'type'.")
    opts = {k: v for k, v in data.items() if k not in ("type", "name")}
    return SourceConfig(type=data["type"], name=data.get("name", data["type"]), options=opts)


def _parse_publisher(data: dict[str, Any]) -> PublisherConfig:
    if "type" not in data:
        raise ConfigError("Each publisher needs a 'type'.")
    opts = {k: v for k, v in data.items() if k != "type"}
    return PublisherConfig(type=data["type"], options=opts)
