import json
from dataclasses import dataclass, field

import pytest

from autoblog.config import BlogConfig, GeneratorConfig
from autoblog.generators.claude import ClaudeGenerator
from autoblog.models import SourceItem


@dataclass
class FakeBlock:
    type: str
    text: str = ""


@dataclass
class FakeMessage:
    stop_reason: str
    content: list = field(default_factory=list)


class FakeStream:
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._message


class FakeMessages:
    def __init__(self, message):
        self._message = message

    def stream(self, **kwargs):
        return FakeStream(self._message)


class FakeClient:
    def __init__(self, message):
        self.messages = FakeMessages(message)


def _generator(monkeypatch, message):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    gen = ClaudeGenerator(GeneratorConfig(), BlogConfig())
    gen.client = FakeClient(message)
    return gen


def _items():
    return [SourceItem(title="Item", url="https://example.com/1", summary="s")]


def test_generate_parses_structured_output(monkeypatch):
    payload = {"title": "My Title", "summary": "sum", "tags": ["x"], "body": "# Body"}
    message = FakeMessage("end_turn", [FakeBlock("text", json.dumps(payload))])
    post = _generator(monkeypatch, message).generate(_items())

    assert post.title == "My Title"
    assert post.slug == "my-title"
    assert post.tags == ["x"]
    assert post.body == "# Body"
    assert post.sources[0].url == "https://example.com/1"


def test_generate_raises_on_refusal(monkeypatch):
    message = FakeMessage("refusal", [])
    with pytest.raises(RuntimeError, match="refused"):
        _generator(monkeypatch, message).generate(_items())


def test_generate_raises_on_truncation(monkeypatch):
    message = FakeMessage("max_tokens", [FakeBlock("text", '{"title": "x"')])
    with pytest.raises(RuntimeError, match="max_tokens"):
        _generator(monkeypatch, message).generate(_items())


def test_generate_raises_on_bad_json(monkeypatch):
    message = FakeMessage("end_turn", [FakeBlock("text", "not json at all")])
    with pytest.raises(RuntimeError, match="not valid JSON"):
        _generator(monkeypatch, message).generate(_items())


def test_generate_requires_items(monkeypatch):
    gen = _generator(monkeypatch, FakeMessage("end_turn", []))
    with pytest.raises(ValueError):
        gen.generate([])
