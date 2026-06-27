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
`SourceItem`s from **all** sources, filters out already-seen items via
`state.SeenStore`, passes the remaining combined list to **one** generator to
produce a single `Post`, then hands that post to **every** configured publisher.
One run = one post synthesized from all *new* source material.

**Dedup / state.** `state.SeenStore` (`src/autoblog/state.py`) is a JSON set of
published item URLs (`config.state_file`, default `.autoblog-state.json`). The
tool is meant to run on a schedule, so this is what prevents duplicate posts
across runs. State is recorded **only after a successful publish** and **not at
all on `dry_run`** (so dry runs stay repeatable); `use_state=False` /
`--no-state` bypasses it entirely. Tests must point `state_file` at a tmp path
(see `tests/test_pipeline.py:_config`) or they'll write to the cwd.

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

### Naver review-package flow (`write` command)

A second, parallel flow for Korean/Naver-blog content, separate from the
RSS→`run` pipeline. `cli.py:_cmd_write` takes a keyword and produces a
human-review package — **it never publishes externally** (Naver's write API was
retired in 2020; the design target is "automate up to paste-ready HTML, human
posts"). Pieces:

- `generators/naver.py:NaverArticleGenerator` — one structured-output API call
  (same SDK conventions as the Claude generator) returning title candidates,
  outline, Markdown body, SEO, and review notes as a typed `Article`
  (`models.py`). **The model does not produce HTML.**
- `publishers/naver_html.py:markdown_to_naver_html` — **deterministic**
  Markdown→inline-styled HTML (소제목 `heading_px`/본문 `body_px`, image
  placeholders). Keep it deterministic and unit-tested; do not move HTML
  rendering into the model. It supports only a Markdown subset (headings,
  paragraphs, `- ` lists, `**bold**`, links, `![alt](IMAGE)`), and the
  generator's prompt is what constrains the model to that subset — change them
  together.
- `validation.py:scan_forbidden` — cheap regex scan (no LLM) for over-promise
  phrasing, merged into `Article.review.warnings` in `_cmd_write`.
- `publishers/naver_artifact.py:NaverArtifactPublisher` — writes the five files
  (`outline.md`, `final.md`, `naver.html`, `seo.json`, `review.md`) to
  `content/YYYY-MM-DD_slug/`.

Config for this flow (`config.forbidden_expressions`, `config.naver`) is
optional: `write` falls back to `config.default_config()` when no config file
exists, so a bare `autoblog write "<keyword>"` works.

### Two generation engines, one deterministic assembler

The Naver package can be produced by either engine, but **both converge on the
same deterministic step**, so keep that step credential-free and testable:

- **`autoblog assemble <article.json>`** (`cli.py:_cmd_assemble`) — takes an
  article JSON (generator schema), builds an `Article` via
  `models.article_from_dict`, merges `validation.scan_forbidden`, and writes the
  5 artifacts via `NaverArtifactPublisher`. **No API call, no key.**
  `models.article_from_dict` is shared by this command and `NaverArticleGenerator`
  — the JSON→Article mapping lives in one place; don't duplicate it.
- **Claude Code subagents** (`.claude/`) — the key-free engine. `.claude/commands/
  blog-write.md` (`/blog-write <키워드>`) orchestrates the `article-writer` and
  `quality-reviewer` subagents (`.claude/agents/*.md`), writes
  `content/_draft/article.json`, then calls `autoblog assemble`. The subagents
  return **JSON only** and do not render HTML — HTML is the deterministic
  renderer's job. Unattended use is `claude -p "/blog-write 키워드"`.
- **Direct API / Bedrock** (`generators/naver.py`) — optional engine for those
  with a key or AWS; produces the same `Article` and is published the same way.

When changing the article JSON shape, update `generators/naver.py:_ARTICLE_SCHEMA`,
`models.article_from_dict`, and the two `.claude/agents/*.md` output specs together.

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

### Provider abstraction (Anthropic vs Bedrock)

Generators do **not** construct the SDK client directly — they call
`generators/client.py:build_client(cfg)` and `resolve_model_id(cfg)`. This is the
single place that switches between the first-party API (`anthropic.Anthropic()`,
`ANTHROPIC_API_KEY`) and AWS Bedrock (`AnthropicBedrockMantle(aws_region=...)`,
AWS IAM). Bedrock model IDs get an `anthropic.` prefix via `resolve_model_id`;
both providers share the same `messages.stream(...)` surface, so generator bodies
are provider-agnostic. `config.GeneratorConfig` carries `provider` + `aws_region`
(validated in `load_config`: `bedrock` requires a region). When adding a
generator, use `build_client`/`resolve_model_id` — never hardcode `anthropic.Anthropic()`.

## Conventions

- Source layout is `src/`-based (`src/autoblog`); imports within the package are
  relative (`from ..models import Post`).
- Dataclasses use `slots=True`. Public stage interfaces are ABCs in each
  package's `base.py`.
- The `webhook` publisher reads credentials from env vars
  (`AUTOBLOG_WEBHOOK_URL` / `AUTOBLOG_WEBHOOK_TOKEN`), never from committed
  config.
