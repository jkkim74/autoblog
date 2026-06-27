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

### Provider: Anthropic API or AWS Bedrock

The generator can run against the first-party Anthropic API (an API key) **or**
AWS Bedrock (AWS IAM credentials — no Anthropic key, billed through AWS). Set it
in the config's `generator` block:

```yaml
generator:
  provider: bedrock        # default: anthropic
  aws_region: us-east-1    # required for bedrock
  model: claude-opus-4-8   # the SDK adds the "anthropic." prefix for Bedrock
```

Install the extra and provide AWS credentials (env vars, shared profile, or an
IAM role) the usual way:

```bash
pip install -e ".[bedrock]"
```

The model must be **enabled in your Bedrock console** for that region, and the
newest models may not be available on Bedrock yet — pick from what your account
offers. Our flow only uses messages, streaming, structured output, and adaptive
thinking/effort, all of which Bedrock supports.

## Run

```bash
# Generate a post but don't publish. Note: this still calls the Claude API
# (generation happens), it just skips publishing and doesn't record state.
autoblog run --config config.yaml --dry-run

# Full run: fetch, generate, publish.
autoblog run --config config.yaml

# Ignore the seen-state file (don't skip prior items, don't record new ones):
autoblog run --config config.yaml --no-state

# Also runs as a module:
python -m autoblog run -c config.yaml
```

Markdown posts are written to the configured `output_dir` (default
`content/posts/`) with YAML front matter, compatible with Hugo/Jekyll/Eleventy.

### Naver review package (`write`)

For Korean / Naver-blog content, `write` takes a single keyword and produces a
**human-review package** — it never publishes anywhere. Naver's blog write API
was retired in 2020, so the realistic target is "automate up to paste-ready
HTML, human reviews and posts."

```bash
autoblog write "클로드 블로그 자동화"            # writes content/<date>_<slug>/
autoblog write "키워드" --dry-run               # generate + scan, write nothing
```

Each run creates `content/YYYY-MM-DD_slug/` with five artifacts:

| File | What |
|---|---|
| `outline.md` | Section outline |
| `final.md` | Markdown body + front matter |
| `naver.html` | Inline-styled HTML to paste into Naver (소제목 22px / 본문 18px) |
| `seo.json` | Title, description, tags, long-tail keywords |
| `review.md` | Title candidates, hype/over-promise warnings, fact-check list, image spots, checklist |

The HTML is rendered **deterministically** from the Markdown (not by the model),
and a regex scan flags over-promise phrasing (무조건/100%/보장 …) into `review.md`.
**Test paste fidelity early:** Naver's SmartEditor can normalize inline styles, so
confirm the 22/18px formatting survives a real paste before relying on it.

### Generation engines

The 5-artifact package can be produced two ways — both end in the same
deterministic `assemble` step (HTML rendering, forbidden-word scan, file layout):

1. **Claude Code subagents (no API key)** — run `/blog-write "<키워드>"` in Claude
   Code. The `article-writer` and `quality-reviewer` subagents draft the content,
   the orchestrator writes `content/_draft/article.json`, then runs `autoblog
   assemble`. Uses your Claude Code login — no Anthropic key, no AWS. For
   unattended scheduling, drive it headlessly: `claude -p "/blog-write 키워드"` on
   a machine where Claude Code is logged in.
2. **Direct API / Bedrock (optional)** — `autoblog write "<키워드>"` calls the model
   via the `anthropic`/Bedrock SDK (needs a key or AWS IAM). Same artifacts.

`autoblog assemble <article.json>` is the shared deterministic step — it makes no
API call and needs no credentials:

```bash
autoblog assemble content/_draft/article.json -o content
```

The input JSON matches the generator schema (`title_candidates`, `outline_md`,
`body_md`, `seo`, `review`).

### Repeated / scheduled runs

`autoblog` is built to run on a schedule (cron, Task Scheduler, CI). It records
the URLs of items it has already published in `state_file` (default
`.autoblog-state.json`) and skips them on later runs, so you don't get duplicate
posts about the same feed entries. Delete that file to start fresh, or pass
`--no-state` to ignore it for one run.

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
