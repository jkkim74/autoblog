---
description: Generate a Naver-style review package from a keyword (human-review, no publish).
argument-hint: <키워드>
---

키워드 **"$ARGUMENTS"** 로 네이버 블로그용 검수 패키지를 생성한다.
최종 발행은 하지 않는다 — 사람이 검수할 산출물만 만든다.

다음 순서로 진행한다:

1. **초안 작성** — `article-writer` 서브에이전트에게 키워드 "$ARGUMENTS" 를 주고
   `title_candidates` / `outline_md` / `body_md` 를 담은 JSON을 받는다.

2. **검토** — `quality-reviewer` 서브에이전트에게 1단계의 `body_md` 를 주고
   `seo` / `review` 를 담은 JSON을 받는다.

3. **JSON 병합** — 두 결과를 하나로 합치고 `keyword` 를 추가한다:
   ```
   {
     "keyword": "$ARGUMENTS",
     "title_candidates": [...], "outline_md": "...", "body_md": "...",
     "seo": {...}, "review": {...}
   }
   ```
   이 객체를 `content/_draft/article.json` 에 UTF-8로 저장한다(폴더 없으면 생성).

4. **조립(결정적)** — 다음을 실행한다:
   ```
   autoblog assemble content/_draft/article.json
   ```
   이 명령이 `content/<날짜>_<slug>/` 아래에 `outline.md` / `final.md` /
   `naver.html`(소제목 22px·본문 18px) / `seo.json` / `review.md` 5종을 만든다.
   (HTML 렌더링과 금지어 스캔은 이 결정적 CLI가 담당하므로 직접 HTML을 만들지 않는다.)

5. **보고** — 생성된 폴더 경로, `review.md` 의 검수 경고·사실확인 항목을 요약하고,
   "발행 전 사람이 검수해야 함"을 알린다.
