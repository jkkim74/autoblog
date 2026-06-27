import json
from dataclasses import dataclass, field

import pytest

from autoblog.config import BlogConfig, GeneratorConfig
from autoblog.generators.naver import NaverArticleGenerator


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


class FakeClient:
    def __init__(self, message):
        self.messages = type("M", (), {"stream": lambda _self, **kw: FakeStream(message)})()


_PAYLOAD = {
    "title_candidates": ["제목A", "제목B"],
    "outline_md": "## 개요",
    "body_md": "## 소제목\n\n본문",
    "seo": {"title": "SEO", "description": "설명", "tags": ["t1"], "longtail": ["l1"]},
    "review": {"warnings": [], "fact_checks": ["확인1"], "image_placeholders": ["상단"]},
}


def _gen(monkeypatch, message):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    gen = NaverArticleGenerator(GeneratorConfig(), BlogConfig())
    gen.client = FakeClient(message)
    return gen


def test_generate_parses_article(monkeypatch):
    message = FakeMessage("end_turn", [FakeBlock("text", json.dumps(_PAYLOAD))])
    article = _gen(monkeypatch, message).generate("키워드")

    assert article.title == "제목A"
    assert article.title_candidates == ["제목A", "제목B"]
    assert article.seo.description == "설명"
    assert article.review.fact_checks == ["확인1"]
    assert article.keyword == "키워드"
    assert article.slug  # allow_unicode keeps a non-empty Korean slug


def test_generate_requires_keyword(monkeypatch):
    gen = _gen(monkeypatch, FakeMessage("end_turn", []))
    with pytest.raises(ValueError):
        gen.generate("   ")


def test_generate_raises_on_truncation(monkeypatch):
    message = FakeMessage("max_tokens", [FakeBlock("text", '{"title_candidates"')])
    with pytest.raises(RuntimeError, match="max_tokens"):
        _gen(monkeypatch, message).generate("키워드")
