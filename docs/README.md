# 문서

## 지금 코드를 설명하는 문서

| 문서 | 내용 |
|---|---|
| [HANDOVER.md](HANDOVER.md) | 인수인계. 구조, 데이터 흐름, 어디를 고치면 무엇이 바뀌나, 함정 |
| [architecture.md](architecture.md) | 모듈·파일별 역할. 옛 경로 → 현재 경로 대응표 포함 |
| [graph_rag.md](graph_rag.md) | 지식베이스 구축 파이프라인 (추출 → 분석 → 적재) |
| [kb-known-issues.md](kb-known-issues.md) | 지식베이스에 남은 문제와 막아 둔 이유 |
| [crawler.md](crawler.md) | 웹 폴백 크롤러 |

설치·실행·API 명세는 저장소 루트의 [README](../README.md) 에 있다.

## 결정 기록

| 문서 | 내용 |
|---|---|
| [adr/0001-hybrid-retrieval.md](adr/0001-hybrid-retrieval.md) | 하이브리드 검색을 택한 이유 (2026-05-01, 개정 주석 있음) |
| [rfc-001-hybrid-search-strategy.md](rfc-001-hybrid-search-strategy.md) | 위 결정의 사전 논의 |

ADR 은 **결정 시점의 기록이다.** 값이 바뀌면 본문을 고치지 말고 개정 주석을 달거나
새 ADR 로 대체한다.

## 평가 실험

[experiments/](experiments/) — 측정 절차와 프로토콜. 코드는 저장소 루트의
[experiments/](../experiments/) 에 있다.

## 보존 문서

제출·발표 시점의 기록이다. 현재 구현과 다를 수 있고, **최신화하지 않는다.**

- [PRD_Campus_Navigator_RAG.md](PRD_Campus_Navigator_RAG.md)
- [semester_project_proposal.md](semester_project_proposal.md)
- [planning/기말발표_기획안_v1.md](planning/기말발표_기획안_v1.md)
- [planning/기말발표_기획안_v2.md](planning/기말발표_기획안_v2.md)
- [planning/document-filling-기획안.md](planning/document-filling-기획안.md) — 미구현 기능 설계안

---

## 수치의 단일 출처

가중치·임계값을 문서에서 인용할 때는 [backend/config/*.yaml](../backend/config/) 을
근거로 삼는다. 코드에는 숫자가 없고, 문서에 박아 둔 숫자는 반드시 낡는다.
