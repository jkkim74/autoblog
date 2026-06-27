"""Command-line interface for autoblog."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, default_config, load_config
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autoblog", description=__doc__)
    parser.add_argument("--version", action="version", version=f"autoblog {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Fetch sources, generate a post, and publish it.")
    run_cmd.add_argument("-c", "--config", default="config.yaml", help="Path to config YAML.")
    run_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate the post but do not publish (still calls the API) and do not "
        "record seen-state.",
    )
    run_cmd.add_argument(
        "--no-state",
        action="store_true",
        help="Ignore the seen-state file: do not skip previously published items "
        "and do not record new ones.",
    )
    run_cmd.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")

    write_cmd = sub.add_parser(
        "write", help="Generate a Naver-style review package from a single keyword."
    )
    write_cmd.add_argument("keyword", help="The topic keyword to write about.")
    write_cmd.add_argument(
        "-c", "--config", default="config.yaml", help="Path to config YAML (optional)."
    )
    write_cmd.add_argument(
        "-o", "--output", default="content", help="Root dir for the article folder."
    )
    write_cmd.add_argument(
        "--dry-run", action="store_true", help="Generate but do not write artifacts."
    )
    write_cmd.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.command == "run":
        return _cmd_run(args)
    if args.command == "write":
        return _cmd_write(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
    _load_dotenv()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    result = run(config, dry_run=args.dry_run, use_state=not args.no_state)
    if result.post is None:
        print("No post generated (no new source items).", file=sys.stderr)
        return 1

    print(f"\n# {result.post.title}\n")
    print(result.post.summary or result.post.body[:200])
    if result.locations:
        print("\nPublished to:")
        for loc in result.locations:
            print(f"  - {loc}")
    return 0


def _cmd_write(args: argparse.Namespace) -> int:
    _load_dotenv()
    # Import here so `--help` / `run` don't pull in the Anthropic SDK.
    from .generators.naver import NaverArticleGenerator
    from .publishers.naver_artifact import NaverArtifactPublisher
    from .validation import scan_forbidden

    if Path(args.config).exists():
        try:
            config = load_config(args.config)
        except ConfigError as exc:
            print(f"Config error: {exc}", file=sys.stderr)
            return 2
    else:
        config = default_config()

    article = NaverArticleGenerator(config.generator, config.blog).generate(args.keyword)
    # Merge the deterministic forbidden-word scan into the human-review warnings.
    article.review.warnings.extend(
        scan_forbidden(article.body_md, config.forbidden_expressions)
    )

    if args.dry_run:
        print(f"\n# {article.title}\n")
        print("후보 제목: " + ", ".join(article.title_candidates))
        print(
            f"\n경고 {len(article.review.warnings)}건 / "
            f"사실확인 {len(article.review.fact_checks)}건 (dry-run: 파일 미생성)"
        )
        return 0

    folder = NaverArtifactPublisher(
        output_root=args.output,
        heading_px=config.naver.heading_px,
        body_px=config.naver.body_px,
    ).publish(article)

    print(f"\n# {article.title}")
    print(f"산출물: {folder}")
    if article.review.warnings:
        print("\n검수 경고:")
        for warning in article.review.warnings:
            print(f"  - {warning}")
    return 0


def _load_dotenv(path: str | Path = ".env") -> None:
    """Minimal .env loader so ANTHROPIC_API_KEY etc. are picked up without extra deps."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


if __name__ == "__main__":
    raise SystemExit(main())
