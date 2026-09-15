# 크롤러

근거가 부족할 때만 도는 웹 폴백. 코드는 [backend/src/yhs/rag/crawler/](../backend/src/yhs/rag/crawler/) 에 있다.

## 파일 역할

- [models.py](../backend/src/yhs/rag/crawler/models.py) — 크롤링 결과 데이터 구조만 정의한다.
- [web_search_client.py](../backend/src/yhs/rag/crawler/web_search_client.py) — 검색, 리다이렉트 해제, 허용 도메인 필터링, 본문 추출.
- [__init__.py](../backend/src/yhs/rag/crawler/__init__.py) — 공개 API 정리.

## 어디서 불리나

- [rag/runtime.py](../backend/src/yhs/rag/runtime.py) — `run_deep_path()` 가 deep path
  이후에도 근거가 부족하면 `search_and_collect()` 를 부른다.
- [api/service.py](../backend/src/yhs/api/service.py) — 서비스 경로의 호출부.
- [rag/query_runner.py](../backend/src/yhs/rag/query_runner.py) — 터미널 경로의 호출부.
- [ingest/pipeline/loader.py](../backend/src/yhs/ingest/pipeline/loader.py) — PDF 와 단일 URL 문서 로딩.

> `infra/freshness.py` 는 빈 스텁이다. 신선도 관리는 이 폴더로 이전됐다.

## 설정

전부 [crawler.yaml](../backend/config/crawler.yaml) 에 있다.

`allowed_sites` 는 **화이트리스트다.** 여기 없는 URL 은 방문하지 않는다.
사이트를 추가할 때는 robots.txt 와 이용약관을 먼저 확인한다.

예산은 `max_depth` 6, `max_pages` 50, `fetch_timeout_sec` 6, `sleep_sec` 0.15.
`cache_ttl_hours` 는 168(7일) — 길게 잡을수록 빠르지만 낡은 공지를 근거로 내놓을
위험이 커진다. 0 이면 캐시를 쓰지 않는다.

환경변수로 덮어쓸 수 있다: `CRAWL_MAX_DEPTH`, `CRAWL_MAX_PAGES`,
`CRAWL_FETCH_TIMEOUT`, `CRAWL_SLEEP_SEC`, `VEC_WEIGHT`, `KW_WEIGHT`.

## 책임 분리

- 검색 결과를 찾는 로직은 `rag/crawler/` 에 둔다.
- 실제 문서 저장과 그래프 적재는 `ingest/` 쪽이다.
- 문서가 적합한지 판단하는 기준은 `rag/` 의 라우팅과 `backend/config/*.yaml` 의
  임계값에서 관리한다.

## 연결성 판단 기준

- 동일 또는 허용된 상위 도메인인가.
- 리다이렉트 후 최종 URL 도 신뢰 가능한가.
- 질문 키워드와 제목·본문의 겹침 정도.
- 기존 저장 문서의 `source_file`, `source_url`, `doc_version` 과 이어지는가.

기준 이하면 재수집 후보로 남기고, 이상이면 인제스트 대상으로 넘긴다.

> JS 렌더링 페이지를 읽으려면 playwright 가 필요하다 (`playwright install chromium`).
> 없어도 크래시는 나지 않고 requests 폴백으로 동작한다 — 수집률만 낮아진다.
