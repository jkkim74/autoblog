from autoblog.config import (
    BlogConfig,
    Config,
    GeneratorConfig,
    PublisherConfig,
    SourceConfig,
)
from autoblog.generators import _REGISTRY as GEN_REGISTRY
from autoblog.generators.base import Generator
from autoblog.models import Post, SourceItem
from autoblog.pipeline import run
from autoblog.sources import _REGISTRY as SRC_REGISTRY
from autoblog.sources.base import Source


class FakeSource(Source):
    def fetch(self):
        return [SourceItem(title="Item 1", url="https://example.com/1", source_name=self.name)]


class FakeGenerator(Generator):
    def __init__(self, cfg, blog):
        self.cfg = cfg

    def generate(self, items):
        return Post(
            title="Generated",
            body="body",
            slug="generated",
            summary="sum",
            sources=items,
        )


def _config(tmp_path):
    return Config(
        blog=BlogConfig(),
        generator=GeneratorConfig(type="fake"),
        sources=[SourceConfig(type="fake", name="Fake", options={})],
        publishers=[PublisherConfig(type="markdown", options={"output_dir": str(tmp_path)})],
    )


def test_run_pipeline_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setitem(SRC_REGISTRY, "fake", FakeSource)
    monkeypatch.setitem(GEN_REGISTRY, "fake", FakeGenerator)

    result = run(_config(tmp_path))

    assert result.items_collected == 1
    assert result.post.title == "Generated"
    assert len(result.locations) == 1
    assert result.locations[0].endswith("-generated.md")


def test_dry_run_skips_publish(tmp_path, monkeypatch):
    monkeypatch.setitem(SRC_REGISTRY, "fake", FakeSource)
    monkeypatch.setitem(GEN_REGISTRY, "fake", FakeGenerator)

    result = run(_config(tmp_path), dry_run=True)

    assert result.post is not None
    assert result.locations == []
    assert not list(tmp_path.glob("*.md"))
