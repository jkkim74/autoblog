# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"          # install with dev tools (pytest, ruff)
pytest                           # run the full test suite (offline, no API key)
pytest tests/test_pipeline.py    # run one test file
pytest tests/test_pipeline.py::test_dry_run_skips_publish   # run one test
ruff check .                     # lint
autoblog run -c config.yaml --dry-run   # generate a post without publishing
python -m autoblog run -c config.yaml   # equivalent module invocation
```

`ANTHROPIC_API_KEY` is required for a real (non-dry-run) generation. The CLI
auto-loads `.env` from the working directory via a minimal parser in
`cli.py:_load_dotenv` (not python-dotenv).

## Architecture

A three-stage pipeline, each stage a swappable plugin with its own registry:

```
sources ──▶ generator (Claude) ──▶ publishers
```

`pipeline.run()` (`src/autoblog/pipeline.py`) is the orchestrator: it collects
`SourceItem`s from **all** sources, passes the combined list to **one**
generator to produce a single `Post`, then hands that post to **every**
configured publisher. One run = one post synthesized from all source material.

The two domain objects in `models.py` are the contracts between stages:
`SourceItem` (raw material in) and `Post` (finished article out). Everything
flows `SourceItem[] -> Post`.

### Plugin registries

Each stage package exposes a `build_*` factory backed by a module-level
`_REGISTRY` dict mapping a config `type` string to a class:

- `sources/__init__.py` → `build_source` (`rss`)
- `generators/__init__.py` → `build_generator` (`claude`)
- `publishers/__init__.py` → `build_publisher` (`markdown`, `webhook`)

To add a plugin: subclass the stage's `base.py` ABC, implement the one abstract
method (`fetch` / `generate` / `publish`), and add a `_REGISTRY` entry. The
tests rely on this — `test_pipeline.py` injects fake `fake` source/generator
types via `monkeypatch.setitem(_REGISTRY, ...)` so the suite runs with no
network or API key. Keep the registries patchable.

### Config flow

`config.py` parses YAML into frozen-ish dataclasses (`Config`, with nested
`BlogConfig`/`GeneratorConfig`/`SourceConfig`/`PublisherConfig`). Source and
publisher configs split their YAML into a known `type`/`name` plus a freeform
`options` dict that is splatted as `**kwargs` into the plugin constructor — so a
plugin's `__init__` signature defines its accepted config keys. Unknown keys on
the typed dataclasses are silently dropped (`_subdict`); unknown plugin options
become a `TypeError` at construction.

### Claude generator specifics

`generators/claude.py` is the only code that calls the Anthropic API. It uses
the official `anthropic` SDK with the model from config (default
`claude-opus-4-8`). Conventions that matter here:

- **Streaming + `get_final_message()`** — posts can be long; streaming avoids
  HTTP timeouts on large `max_tokens`.
- **Adaptive thinking** — `thinking={"type": "adaptive"}`. Do not use
  `budget_tokens` (rejected by current Opus models).
- **`effort`** goes inside `output_config` alongside `format`.
- **Structured outputs** — `output_config.format` with a JSON schema guarantees
  the response parses; the body comes back as the `body` field, in Markdown.
- Always check `stop_reason == "refusal"` before reading content.

When editing this file, prefer the current SDK shapes above over any older
patterns (e.g. `output_format`, `budget_tokens`, non-streaming large outputs).

## Conventions

- Source layout is `src/`-based (`src/autoblog`); imports within the package are
  relative (`from ..models import Post`).
- Dataclasses use `slots=True`. Public stage interfaces are ABCs in each
  package's `base.py`.
- The `webhook` publisher reads credentials from env vars
  (`AUTOBLOG_WEBHOOK_URL` / `AUTOBLOG_WEBHOOK_TOKEN`), never from committed
  config.
