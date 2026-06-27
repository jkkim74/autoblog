# autoblog

An auto-blogging tool. It pulls raw material from **sources** (RSS feeds),
uses a **generator** (Claude) to synthesize an original post, and delivers it
through one or more **publishers** (Markdown files and/or an HTTP webhook to a
platform).

## How it works

```
sources ──▶ generator (Claude) ──▶ publishers
 (RSS)        rewrite/summarize       (Markdown, webhook)
```

One `autoblog run` collects items from every configured source, generates a
single post from the combined material, and publishes it. The three stages are
pluggable: each has a small registry, so adding a new source/generator/publisher
is a class plus one registry entry.

## Install

Requires Python 3.12+.

```bash
pip install -e ".[dev]"
```

## Configure

```bash
cp config.example.yaml config.yaml   # edit sources, style, publishers
cp .env.example .env                 # add ANTHROPIC_API_KEY
```

The generator uses the Anthropic API; set `ANTHROPIC_API_KEY` in `.env` (loaded
automatically) or your environment.

## Run

```bash
# Generate a post but don't publish (no API key needed only if you stub the generator):
autoblog run --config config.yaml --dry-run

# Full run: fetch, generate, publish.
autoblog run --config config.yaml

# Also runs as a module:
python -m autoblog run -c config.yaml
```

Markdown posts are written to the configured `output_dir` (default
`content/posts/`) with YAML front matter, compatible with Hugo/Jekyll/Eleventy.

## Test

```bash
pytest            # unit tests (no network/API calls)
ruff check .      # lint
```

The pipeline and config tests stub the source and generator, so the suite runs
offline with no API key.

## Extending

- **New source**: subclass `autoblog.sources.base.Source`, implement `fetch()`,
  register it in `autoblog/sources/__init__.py`.
- **New generator**: subclass `autoblog.generators.base.Generator`, implement
  `generate()`, register it in `autoblog/generators/__init__.py`.
- **New publisher** (e.g. WordPress, Ghost, Dev.to): subclass
  `autoblog.publishers.base.Publisher`, implement `publish()`, register it in
  `autoblog/publishers/__init__.py`. The included `webhook` publisher POSTs post
  JSON to any endpoint and is often enough behind a thin adapter.
