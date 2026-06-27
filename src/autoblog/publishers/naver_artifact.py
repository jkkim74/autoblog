"""Write a Naver review package: the 5 artifacts a human needs before posting.

Lays down ``content/YYYY-MM-DD_slug/`` with outline.md, final.md, naver.html,
seo.json, and review.md. Nothing is published anywhere external — the human
pastes ``naver.html`` into Naver after checking ``review.md``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import yaml

from ..models import Article
from .naver_html import markdown_to_naver_html


class NaverArtifactPublisher:
    def __init__(
        self, output_root: str = "content", heading_px: int = 22, body_px: int = 18
    ) -> None:
        self.output_root = Path(output_root)
        self.heading_px = heading_px
        self.body_px = body_px

    def publish(self, article: Article) -> str:
        folder = self._make_folder(article)

        (folder / "outline.md").write_text(article.outline_md + "\n", encoding="utf-8")
        (folder / "final.md").write_text(self._final_md(article), encoding="utf-8")
        (folder / "naver.html").write_text(
            markdown_to_naver_html(
                article.body_md, heading_px=self.heading_px, body_px=self.body_px
            )
            + "\n",
            encoding="utf-8",
        )
        (folder / "seo.json").write_text(
            json.dumps(asdict(article.seo), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (folder / "review.md").write_text(self._review_md(article), encoding="utf-8")
        return str(folder)

    def _make_folder(self, article: Article) -> Path:
        date = article.created_at.strftime("%Y-%m-%d")
        folder = self.output_root / f"{date}_{article.slug}"
        # Avoid clobbering a previous run for the same date+slug.
        counter = 2
        while folder.exists():
            folder = self.output_root / f"{date}_{article.slug}-{counter}"
            counter += 1
        folder.mkdir(parents=True)
        return folder

    def _final_md(self, article: Article) -> str:
        front_matter = {
            "title": article.title,
            "date": article.created_at.isoformat(),
            "keyword": article.keyword,
            "description": article.seo.description,
            "tags": article.seo.tags,
        }
        fm = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{fm}\n---\n\n{article.body_md}\n"

    def _review_md(self, article: Article) -> str:
        lines = [f"# 검수 패키지 — {article.title}", ""]
        lines += ["## 추천 제목", ""]
        lines += [f"{i}. {t}" for i, t in enumerate(article.title_candidates, 1)] or ["(없음)"]
        lines += ["", "## 위험/과장 표현", ""]
        lines += [f"- {w}" for w in article.review.warnings] or ["- 없음"]
        lines += ["", "## 사실 확인 필요", ""]
        lines += [f"- {c}" for c in article.review.fact_checks] or ["- 없음"]
        lines += ["", "## 이미지 삽입 위치", ""]
        lines += [f"- {p}" for p in article.review.image_placeholders] or ["- 없음"]
        lines += [
            "",
            "## 발행 전 체크리스트",
            "",
            "- [ ] 제목 확정",
            "- [ ] 사실관계 확인",
            "- [ ] 과장/광고성 표현 제거",
            "- [ ] 이미지 삽입",
            "- [ ] naver.html 붙여넣기 후 서식 확인",
        ]
        return "\n".join(lines) + "\n"
