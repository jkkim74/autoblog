"""Load and validate the YAML config into typed dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .validation import DEFAULT_FORBIDDEN


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
    # Which SDK client to use: "anthropic" (API key) or "bedrock" (AWS IAM).
    provider: str = "anthropic"
    # Required when provider == "bedrock".
    aws_region: str = ""


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
class NaverConfig:
    heading_px: int = 22
    body_px: int = 18


@dataclass(slots=True)
class Config:
    blog: BlogConfig
    generator: GeneratorConfig
    sources: list[SourceConfig]
    publishers: list[PublisherConfig]
    # File used to remember which source items were already published.
    state_file: str = ".autoblog-state.json"
    # Over-promise / hype phrases flagged for human review (Naver flow).
    forbidden_expressions: list[str] = field(
        default_factory=lambda: list(DEFAULT_FORBIDDEN)
    )
    naver: NaverConfig = field(default_factory=NaverConfig)


def default_config() -> Config:
    """A usable Config with no sources/publishers, for the keyword `write` flow."""
    return Config(blog=BlogConfig(), generator=GeneratorConfig(), sources=[], publishers=[])


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
    if generator.provider == "bedrock" and not generator.aws_region:
        raise ConfigError("generator.provider 'bedrock' requires 'aws_region'.")

    sources = [_parse_source(s) for s in raw.get("sources", [])]
    if not sources:
        raise ConfigError("At least one source is required under 'sources'.")

    publishers = [_parse_publisher(p) for p in raw.get("publishers", [])]
    if not publishers:
        raise ConfigError("At least one publisher is required under 'publishers'.")

    state_file = raw.get("state_file", ".autoblog-state.json")
    forbidden = raw.get("forbidden_expressions") or list(DEFAULT_FORBIDDEN)
    naver = NaverConfig(**_subdict(raw.get("naver", {}), NaverConfig))

    return Config(
        blog=blog,
        generator=generator,
        sources=sources,
        publishers=publishers,
        state_file=state_file,
        forbidden_expressions=forbidden,
        naver=naver,
    )


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
