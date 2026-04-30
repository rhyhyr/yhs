# Architecture Decision Records (ADR)

이 폴더는 프로젝트의 주요 기술 결정 사항을 기록합니다.

## ADR이란?

ADR(Architecture Decision Record)은 프로젝트에서 내린 중요한 기술적 결정과 그 배경, 대안, 결과를 문서화한 기록입니다. 나중에 "왜 이렇게 했지?"라는 질문에 답할 수 있도록 남겨둡니다.

## 파일 목록

| 번호 | 제목 | 상태 |
|---|---|---|
| [ADR-0001](0001-hybrid-retrieval.md) | 하이브리드 검색 전략 채택 | Accepted |

## ADR 상태 정의

- **Proposed** — 검토 중
- **Accepted** — 채택됨
- **Deprecated** — 더 이상 유효하지 않음
- **Superseded** — 다른 ADR로 대체됨

## 새 ADR 작성 방법

1. `template.md`를 복사해 `NNNN-제목.md` 형식으로 저장
2. 내용 작성 후 이 README의 파일 목록에 추가
3. PR을 통해 팀 리뷰 후 병합

---

> 📝 이 문서는 작성 과정에서 생성형 AI(Claude)의 도움을 받아 작성되었습니다.
