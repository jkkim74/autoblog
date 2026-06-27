import httpx

from autoblog.sources import rss
from autoblog.sources.rss import RSSSource

_FEED = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Test Feed</title>
  <item><title>One</title><link>https://example.com/1</link><description>d1</description></item>
  <item><title>Two</title><link>https://example.com/2</link><description>d2</description></item>
</channel></rss>"""


class FakeResp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_fetch_parses_entries_and_respects_max_items(monkeypatch):
    monkeypatch.setattr(rss.httpx, "get", lambda url, **kw: FakeResp(_FEED))
    items = RSSSource(name="Test", url="https://example.com/feed", max_items=1).fetch()

    assert len(items) == 1
    assert items[0].title == "One"
    assert items[0].url == "https://example.com/1"
    assert items[0].summary == "d1"
    assert items[0].source_name == "Test"


def test_fetch_returns_empty_on_http_error(monkeypatch):
    def boom(url, **kw):
        raise httpx.ConnectError("nope")

    monkeypatch.setattr(rss.httpx, "get", boom)
    items = RSSSource(name="Test", url="https://example.com/feed").fetch()

    assert items == []
