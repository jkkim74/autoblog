import json

from autoblog.cli import main


def _write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return path


def test_assemble_writes_five_artifacts_and_merges_scan(tmp_path):
    article = {
        "keyword": "테스트",
        "title_candidates": ["제목"],
        "outline_md": "## 개요",
        "body_md": "## 소제목\n\n무조건 좋은 방법입니다.",
        "seo": {"title": "t", "description": "d", "tags": ["a"], "longtail": ["b"]},
        "review": {"warnings": [], "fact_checks": [], "image_placeholders": []},
    }
    json_path = _write_json(tmp_path / "art.json", article)
    out = tmp_path / "content"

    rc = main(["assemble", str(json_path), "-o", str(out)])
    assert rc == 0

    files = {p.name: p for p in out.rglob("*") if p.is_file()}
    assert {"outline.md", "final.md", "naver.html", "seo.json", "review.md"} <= set(files)

    html = files["naver.html"].read_text(encoding="utf-8")
    assert "font-size:22px" in html and "font-size:18px" in html

    review = files["review.md"].read_text(encoding="utf-8")
    assert "무조건" in review  # deterministic forbidden scan merged into review


def test_assemble_rejects_missing_body(tmp_path):
    json_path = _write_json(tmp_path / "bad.json", {"title_candidates": []})
    rc = main(["assemble", str(json_path), "-o", str(tmp_path / "out")])
    assert rc == 2
