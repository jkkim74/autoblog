"""Publish posts to a platform by POSTing JSON to an HTTP endpoint.

Intentionally generic: point it at your CMS's REST API, a serverless function,
or a service like Dev.to / Ghost behind a small adapter. Credentials are read
from the environment, never hard-coded in config.
"""

from __future__ import annotations

import os

import httpx

from ..models import Post
from .base import Publisher


class WebhookPublisher(Publisher):
    def __init__(
        self,
        url: str | None = None,
        url_env: str = "AUTOBLOG_WEBHOOK_URL",
        token_env: str = "AUTOBLOG_WEBHOOK_TOKEN",
        timeout: float = 30.0,
    ) -> None:
        self.url = url or os.environ.get(url_env)
        if not self.url:
            raise ValueError(
                f"Webhook publisher needs a URL: set 'url' in config or the {url_env} env var."
            )
        self.token = os.environ.get(token_env)
        self.timeout = timeout

    def publish(self, post: Post) -> str:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {
            "title": post.title,
            "slug": post.slug,
            "summary": post.summary,
            "tags": post.tags,
            "body": post.body,
            "created_at": post.created_at.isoformat(),
            "sources": [{"title": s.title, "url": s.url} for s in post.sources],
        }
        resp = httpx.post(self.url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return f"{self.url} ({resp.status_code})"
