import json
from pathlib import Path

from autoblog.models import Article, ReviewNotes, Seo
from autoblog.publishers.naver_artifact import NaverArtifactPublisher


def _article():
    return Article(
        keyword="키워드",
        title="제목",
        slug="제목",
        outline_md="## 개요",
        body_md="## 소제목\n\n본문입니다.",
        title_candidates=["제목", "제목2"],
        seo=Seo(title="t", description="d", tags=["a"], longtail=["b"]),
        review=ReviewNotes(warnings=["경고1"], fact_checks=["확인1"], image_placeholders=["상단"]),
    )


def test_publish_writes_five_artifacts(tmp_path):
    folder = Path(NaverArtifactPublisher(output_root=str(tmp_path)).publish(_article()))

    for name in ("outline.md", "final.md", "naver.html", "seo.json", "review.md"):
        assert (folder / name).exists(), name

    html = (folder / "naver.html").read_text(encoding="utf-8")
    assert "font-size:22px" in html  # heading
    assert "font-size:18px" in html  # body

    review = (folder / "review.md").read_text(encoding="utf-8")
    assert "경고1" in review
    assert "체크리스트" in review

    seo = json.loads((folder / "seo.json").read_text(encoding="utf-8"))
    assert seo["description"] == "d"


def test_publish_avoids_collision(tmp_path):
    publisher = NaverArtifactPublisher(output_root=str(tmp_path))
    first = publisher.publish(_article())
    second = publisher.publish(_article())
    assert first != second
