"""Orchestration: fetch sources -> generate a post -> publish it."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Config
from .generators import build_generator
from .models import Post, SourceItem
from .publishers import build_publisher
from .sources import build_source
from .state import SeenStore

log = logging.getLogger("autoblog")


@dataclass(slots=True)
class RunResult:
    post: Post | None
    locations: list[str]
    items_collected: int


def run(config: Config, *, dry_run: bool = False, use_state: bool = True) -> RunResult:
    """Execute one full pipeline pass.

    A single post is generated from the combined material of all sources. With
    dry_run=True, the post is generated but not published (and seen-state is not
    recorded). With use_state=True, items already published in a previous run
    are skipped, so repeated/scheduled runs don't produce duplicate posts.
    """
    store = SeenStore(config.state_file) if use_state else None

    items = _collect_items(config)
    if store is not None:
        before = len(items)
        items = [item for item in items if not store.is_seen(item.url)]
        skipped = before - len(items)
        if skipped:
            log.info("Skipped %d already-published item(s).", skipped)

    if not items:
        log.warning("No new source items; nothing to generate.")
        return RunResult(post=None, locations=[], items_collected=0)

    generator = build_generator(config.generator, config.blog)
    log.info("Generating post from %d source item(s) with %s...", len(items), config.generator.model)
    post = generator.generate(items)
    log.info("Generated post: %s", post.title)

    if dry_run:
        log.info("Dry run: skipping publish and state update.")
        return RunResult(post=post, locations=[], items_collected=len(items))

    locations: list[str] = []
    for pub_cfg in config.publishers:
        publisher = build_publisher(pub_cfg)
        location = publisher.publish(post)
        log.info("Published via %s -> %s", pub_cfg.type, location)
        locations.append(location)

    # Only record state after a successful publish, so a failure mid-run can be
    # retried against the same items.
    if store is not None:
        store.add(item.url for item in items)
        store.save()

    return RunResult(post=post, locations=locations, items_collected=len(items))


def _collect_items(config: Config) -> list[SourceItem]:
    items: list[SourceItem] = []
    for src_cfg in config.sources:
        source = build_source(src_cfg)
        try:
            fetched = source.fetch()
        except Exception:  # noqa: BLE001 - one bad source shouldn't kill the run
            log.exception("Source %r failed; skipping.", src_cfg.name)
            continue
        log.info("Source %r returned %d item(s).", src_cfg.name, len(fetched))
        items.extend(fetched)
    return items
