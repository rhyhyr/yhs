# Crawler Responsibility Map

이 폴더는 외부 문서 수집과 URL 기반 크롤링 관련 책임만 둔다.

## 파일 역할

- [models.py](models.py): 크롤링 결과를 담는 데이터 구조만 정의한다.
- [web_search_client.py](web_search_client.py): 검색, 리다이렉트 해제, 허용 도메인 필터링, 본문 추출을 담당한다.
- [__init__.py](__init__.py): 외부에서 크롤러를 한 번에 가져다 쓸 수 있게 공개 API를 정리한다.

## 현재 코드와의 연결

- [agent/agent_runtime.py](../agent_runtime.py): 질의 라우팅과 외부 검색 진입점에서 크롤러를 호출한다.
- [graph_rag/pipeline/loader.py](../../graph_rag/pipeline/loader.py): PDF와 단일 URL 문서 로딩을 담당한다.
- [graph_rag/scheduler/freshness.py](../../graph_rag/scheduler/freshness.py): 등록된 URL의 변경 감지와 재검토 플래그를 담당한다.
- [graph_rag/pipeline/ingestor.py](../../graph_rag/pipeline/ingestor.py): 수집된 청크를 그래프 DB에 적재한다.

## 책임 분리 기준

- 검색 결과를 찾는 로직은 이 폴더에 둔다.
- 실제 문서 저장과 그래프 적재는 `graph_rag` 쪽에 둔다.
- 문서가 적합한지 판단하는 기준은 `agent`의 라우팅과 `graph_rag`의 임계값 설정에서 관리한다.

## 연결성 판단 기준

- 동일 또는 허용된 상위 도메인인지 확인한다.
- 최종 도착 URL이 리다이렉트 후에도 신뢰 가능한지 확인한다.
- 질문 키워드와 제목/본문의 겹침 정도를 비교한다.
- 기존 저장 문서의 `source_file`, `source_url`, `doc_version`과 이어지는지 본다.
- 기준 이하이면 재수집 후보로 남기고, 기준 이상이면 인제스트 대상으로 넘긴다.