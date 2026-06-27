import pytest

from autoblog.config import ConfigError, load_config


def _write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_minimal_config(tmp_path):
    cfg = load_config(
        _write(
            tmp_path,
            """
blog:
  title: Test Blog
generator:
  type: claude
  model: claude-opus-4-8
sources:
  - type: rss
    name: Example
    url: https://example.com/feed
    max_items: 2
publishers:
  - type: markdown
    output_dir: out
""",
        )
    )
    assert cfg.blog.title == "Test Blog"
    assert cfg.generator.model == "claude-opus-4-8"
    assert cfg.sources[0].type == "rss"
    assert cfg.sources[0].options == {"url": "https://example.com/feed", "max_items": 2}
    assert cfg.publishers[0].options == {"output_dir": "out"}


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.yaml")


def test_requires_sources(tmp_path):
    with pytest.raises(ConfigError):
        load_config(
            _write(
                tmp_path,
                """
generator:
  type: claude
publishers:
  - type: markdown
""",
            )
        )


def test_bedrock_requires_aws_region(tmp_path):
    with pytest.raises(ConfigError):
        load_config(
            _write(
                tmp_path,
                """
generator:
  type: claude
  provider: bedrock
sources:
  - type: rss
    name: X
    url: u
publishers:
  - type: markdown
""",
            )
        )


def test_bedrock_with_region_ok(tmp_path):
    cfg = load_config(
        _write(
            tmp_path,
            """
generator:
  type: claude
  provider: bedrock
  aws_region: us-east-1
sources:
  - type: rss
    name: X
    url: u
publishers:
  - type: markdown
""",
        )
    )
    assert cfg.generator.provider == "bedrock"
    assert cfg.generator.aws_region == "us-east-1"


def test_unknown_keys_are_ignored(tmp_path):
    cfg = load_config(
        _write(
            tmp_path,
            """
blog:
  title: T
  bogus_field: 123
generator:
  type: claude
sources:
  - type: rss
    name: X
    url: u
publishers:
  - type: markdown
""",
        )
    )
    assert cfg.blog.title == "T"
