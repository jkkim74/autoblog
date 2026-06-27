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


@dataclass(slots=True)
class Seo:
    """SEO metadata for a Naver-style article."""

    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    longtail: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReviewNotes:
    """Human-review notes attached to an article (never auto-published)."""

    warnings: list[str] = field(default_factory=list)
    fact_checks: list[str] = field(default_factory=list)
    image_placeholders: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Article:
    """A Korean/Naver-style article with the full review-package payload.

    Richer than Post: carries title candidates, an outline, SEO metadata, and
    review notes so a human can vet it before pasting into Naver.
    """

    keyword: str
    title: str
    slug: str
    outline_md: str
    body_md: str
    title_candidates: list[str] = field(default_factory=list)
    seo: Seo = field(default_factory=Seo)
    review: ReviewNotes = field(default_factory=ReviewNotes)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
