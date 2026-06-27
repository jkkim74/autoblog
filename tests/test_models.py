from autoblog.models import article_from_dict


def test_article_from_dict_maps_fields():
    data = {
        "title_candidates": ["제목A", "제목B"],
        "outline_md": "## 개요",
        "body_md": "본문",
        "seo": {"title": "t", "description": "d", "tags": ["x"], "longtail": ["l"]},
        "review": {"warnings": ["w"], "fact_checks": ["f"], "image_placeholders": ["i"]},
    }
    art = article_from_dict(data, "키워드")

    assert art.title == "제목A"
    assert art.keyword == "키워드"
    assert art.title_candidates == ["제목A", "제목B"]
    assert art.seo.tags == ["x"]
    assert art.review.warnings == ["w"]
    assert art.slug  # allow_unicode -> non-empty Korean slug


def test_article_from_dict_defaults_to_keyword():
    art = article_from_dict({"body_md": "본문"}, "키워드")
    assert art.title == "키워드"  # no candidates -> keyword
    assert art.outline_md == ""
    assert art.seo.title == "키워드"
    assert art.slug
