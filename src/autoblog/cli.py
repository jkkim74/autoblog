"""Command-line interface for autoblog."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autoblog", description=__doc__)
    parser.add_argument("--version", action="version", version=f"autoblog {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Fetch sources, generate a post, and publish it.")
    run_cmd.add_argument("-c", "--config", default="config.yaml", help="Path to config YAML.")
    run_cmd.add_argument(
        "--dry-run", action="store_true", help="Generate the post but do not publish."
    )
    run_cmd.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.command == "run":
        return _cmd_run(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
    _load_dotenv()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    result = run(config, dry_run=args.dry_run)
    if result.post is None:
        print("No post generated (no source items).", file=sys.stderr)
        return 1

    print(f"\n# {result.post.title}\n")
    print(result.post.summary or result.post.body[:200])
    if result.locations:
        print("\nPublished to:")
        for loc in result.locations:
            print(f"  - {loc}")
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
