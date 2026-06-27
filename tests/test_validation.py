from autoblog.validation import scan_forbidden


def test_detects_default_forbidden_phrases():
    text = "이 방법은 무조건 100% 수익 보장입니다."
    warnings = scan_forbidden(text)
    joined = " ".join(warnings)
    assert "무조건" in joined
    assert "100%" in joined
    assert "보장" in joined


def test_clean_text_has_no_warnings():
    assert scan_forbidden("오늘은 차분하게 정리해 보겠습니다.") == []


def test_custom_patterns():
    assert scan_forbidden("대박 정보", ["대박"]) == ["과장/금지 표현 감지: '대박'"]
