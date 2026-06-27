import pytest

from autoblog.models import Post, SourceItem
from autoblog.publishers import webhook
from autoblog.publishers.webhook import WebhookPublisher


class FakeResp:
    status_code = 201

    def raise_for_status(self):
        pass


def _post():
    return Post(
        title="T",
        body="body",
        slug="t",
        tags=["a"],
        summary="s",
        sources=[SourceItem(title="Src", url="https://example.com")],
    )


def test_publish_posts_json_with_auth(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers)
        return FakeResp()

    monkeypatch.setenv("AUTOBLOG_WEBHOOK_TOKEN", "secret")
    monkeypatch.setattr(webhook.httpx, "post", fake_post)

    location = WebhookPublisher(url="https://example.com/api").publish(_post())

    assert "201" in location
    assert captured["url"] == "https://example.com/api"
    assert captured["json"]["title"] == "T"
    assert captured["json"]["sources"][0]["url"] == "https://example.com"
    assert captured["headers"]["Authorization"] == "Bearer secret"


def test_requires_a_url(monkeypatch):
    monkeypatch.delenv("AUTOBLOG_WEBHOOK_URL", raising=False)
    with pytest.raises(ValueError):
        WebhookPublisher()
