from autoblog.publishers.naver_html import markdown_to_naver_html


def test_heading_uses_heading_px():
    html = markdown_to_naver_html("## 소제목", heading_px=22, body_px=18)
    assert "<h3" in html
    assert "font-size:22px" in html
    assert "소제목" in html


def test_paragraph_uses_body_px():
    html = markdown_to_naver_html("본문 문장입니다.", body_px=18)
    assert "<p" in html
    assert "font-size:18px" in html


def test_bold_and_link_inline():
    html = markdown_to_naver_html("**굵게** 그리고 [링크](https://example.com)")
    assert "<strong>굵게</strong>" in html
    assert '<a href="https://example.com">링크</a>' in html


def test_bullet_list():
    html = markdown_to_naver_html("- 첫째\n- 둘째")
    assert html.count("<li") == 2
    assert "<ul" in html


def test_image_placeholder():
    html = markdown_to_naver_html("![풍경 사진](IMAGE)")
    assert "이미지 자리: 풍경 사진" in html
    assert "dashed" in html


def test_html_is_escaped():
    html = markdown_to_naver_html("a < b & c")
    assert "&lt;" in html
    assert "&amp;" in html


def test_blocks_split_on_blank_lines():
    html = markdown_to_naver_html("첫 문단\n\n둘째 문단")
    assert html.count("<p") == 2
