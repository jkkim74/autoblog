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
        state_file=str(tmp_path / "state.json"),
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


def test_state_dedup_skips_already_published(tmp_path, monkeypatch):
    monkeypatch.setitem(SRC_REGISTRY, "fake", FakeSource)
    monkeypatch.setitem(GEN_REGISTRY, "fake", FakeGenerator)
    config = _config(tmp_path)

    first = run(config)
    assert first.post is not None  # first run publishes

    second = run(config)
    assert second.post is None  # same item is now seen -> nothing new
    assert second.items_collected == 0


def test_dry_run_does_not_record_state(tmp_path, monkeypatch):
    monkeypatch.setitem(SRC_REGISTRY, "fake", FakeSource)
    monkeypatch.setitem(GEN_REGISTRY, "fake", FakeGenerator)
    config = _config(tmp_path)

    run(config, dry_run=True)
    # A real run afterwards should still see the item as new.
    result = run(config)
    assert result.post is not None


def test_no_state_disables_dedup(tmp_path, monkeypatch):
    monkeypatch.setitem(SRC_REGISTRY, "fake", FakeSource)
    monkeypatch.setitem(GEN_REGISTRY, "fake", FakeGenerator)
    config = _config(tmp_path)

    run(config, use_state=False)
    second = run(config, use_state=False)
    assert second.post is not None  # no state kept -> item is "new" every time
