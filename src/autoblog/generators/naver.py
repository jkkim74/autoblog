"""Korean / Naver-style article generator (direct Anthropic API).

Given a single keyword, produces a full review package in one structured-output
call: title candidates, an outline, the Markdown body, SEO metadata, and review
notes. HTML is intentionally NOT produced here — it is rendered deterministically
by ``publishers/naver_html.py`` so the styling is testable and consistent.
"""

from __future__ import annotations

import json

from slugify import slugify

from ..config import BlogConfig, GeneratorConfig
from ..models import Article, ReviewNotes, Seo
from .client import build_client, resolve_model_id

_ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title_candidates": {
            "type": "array",
            "items": {"type": "string"},
            "description": "5 distinct title options, best first.",
        },
        "outline_md": {"type": "string", "description": "Section outline in Markdown."},
        "body_md": {
            "type": "string",
            "description": (
                "The article body in simple Markdown: '##'/'###' headings, blank-line "
                "separated paragraphs, '- ' bullet lists, '**bold**', '[text](url)' "
                "links, and image placeholders written as '![설명](IMAGE)'."
            ),
        },
        "seo": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "longtail": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "description", "tags", "longtail"],
            "additionalProperties": False,
        },
        "review": {
            "type": "object",
            "properties": {
                "warnings": {"type": "array", "items": {"type": "string"}},
                "fact_checks": {"type": "array", "items": {"type": "string"}},
                "image_placeholders": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["warnings", "fact_checks", "image_placeholders"],
            "additionalProperties": False,
        },
    },
    "required": ["title_candidates", "outline_md", "body_md", "seo", "review"],
    "additionalProperties": False,
}


class NaverArticleGenerator:
    def __init__(self, cfg: GeneratorConfig, blog: BlogConfig) -> None:
        self.cfg = cfg
        self.blog = blog
        self.client = build_client(cfg)
        self.model_id = resolve_model_id(cfg)

    def generate(self, keyword: str) -> Article:
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("NaverArticleGenerator.generate requires a non-empty keyword.")

        system = (
            "당신은 한국어 네이버 블로그 글을 쓰는 전문 작가입니다. 주어진 키워드로 "
            "독자에게 실질적으로 도움이 되는 오리지널 글을 작성합니다. 짧은 문장과 "
            "명확한 소제목을 사용하고, 3~4문단마다 호흡을 둡니다. 과장된 수익 보장 "
            "표현과 출처 없는 수치 단정은 사용하지 않습니다. 사실관계가 불확실한 "
            "문장은 review.fact_checks에 따로 표시합니다. "
            f"문체 가이드: {self.blog.style.strip()} "
            f"본문 분량은 약 {self.blog.target_words} 단어를 목표로 합니다."
        )
        user = (
            f"키워드: {keyword}\n\n"
            "요청한 JSON 스키마에 맞춰 글을 생성하세요. body_md는 위에 설명된 단순 "
            "Markdown 형식만 사용하고, 이미지가 들어갈 자리는 '![설명](IMAGE)'로 표시하세요."
        )

        with self.client.messages.stream(
            model=self.model_id,
            max_tokens=16000,
            system=system,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.cfg.effort,
                "format": {"type": "json_schema", "schema": _ARTICLE_SCHEMA},
            },
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            raise RuntimeError("Claude refused to generate this article (safety stop).")
        if message.stop_reason == "max_tokens":
            raise RuntimeError(
                "Generation hit the max_tokens limit, so the JSON output is truncated. "
                "Lower 'target_words' or raise max_tokens in NaverArticleGenerator."
            )

        text = next((b.text for b in message.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Claude returned output that is not valid JSON (stop_reason="
                f"{message.stop_reason!r}): {exc}"
            ) from exc

        candidates = list(data.get("title_candidates", []))
        title = candidates[0] if candidates else keyword
        seo = data["seo"]
        review = data["review"]

        return Article(
            keyword=keyword,
            title=title,
            slug=_slug(title) or _slug(keyword) or "article",
            outline_md=data["outline_md"],
            body_md=data["body_md"],
            title_candidates=candidates,
            seo=Seo(
                title=seo.get("title", title),
                description=seo.get("description", ""),
                tags=list(seo.get("tags", [])),
                longtail=list(seo.get("longtail", [])),
            ),
            review=ReviewNotes(
                warnings=list(review.get("warnings", [])),
                fact_checks=list(review.get("fact_checks", [])),
                image_placeholders=list(review.get("image_placeholders", [])),
            ),
        )


def _slug(value: str) -> str:
    # allow_unicode keeps Korean readable in folder names instead of dropping it.
    return slugify(value, allow_unicode=True)[:80]
