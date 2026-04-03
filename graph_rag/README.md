# graph_rag

유학생(비자/체류/행정) 관련 문서를 그래프로 구조화하고,
문서를 데이터베이스에 저장하는 Graph RAG 모듈입니다.

한 줄 요약:
- 문서(PDF) -> 엔티티/관계 추출 -> Neo4j 그래프 저장

---
## 이 프로젝트의 의도

이 모듈은 "유학생 지원 도메인 전용 지식 엔진"입니다.

단순 키워드 검색이 아니라,
- 비자 간 전환 조건
- 필요 서류
- 막히는 조건(BLOCKS)
- 단계형 절차

같은 관계 정보를 그래프로 저장해 더 정확한 검색을 목표로 합니다.

---

## 전체 흐름 (쉽게 보기)

### 1) 인제스트: 지식 구축

main.py ingest 모드에서 아래 순서로 실행됩니다.

PDFLoader -> clean_text -> chunk_document -> HybridExtractor -> GraphIngestor -> Embedder

- Loader: PDF에서 페이지별 텍스트 수집
- Cleaner: 공백/줄바꿈 정리
- Chunker: 텍스트를 의미 단위로 분할
- Extractor: 규칙 + LLM으로 엔티티/관계 추출
- Ingestor: 정규화, 중복 처리 후 Neo4j에 upsert
- Embedder: 청크 임베딩 생성(벡터 검색용)

## LLM 모델 
PDF 추출 - OpenAI GPT-4o - 유료
임베딩 - BAAI/bge-m3 - 무료

## 폴더별 역할

- main.py
  - 실행 진입점 (ingest, query, embed-update, freshness)
- config.py
  - 경로, 모델, 임계값 등 공통 설정
- schema/types.py
  - 노드/엣지/검색 결과 데이터 계약

- pipeline/
  - 로딩/정제/청킹/추출/적재 파이프라인
- db/graph_store.py
  - Neo4j 연결 및 Cypher 기반 저장/조회 레이어
- embedding/embedder.py
  - 임베딩 생성 및 코사인 유사도 계산
- llm/
  - KB 구축용 추출 클라이언트
- scheduler/freshness.py
  - 문서 변경 감지 후 needs_review 플래그 처리

---

## 빠른 실행 예시

프로젝트 루트에서 실행:

```bash
# PDF 인제스트 실행
python main.py --ingest

# 임베딩 누락분만 업데이트
python main.py --embed-update
```

옵션 예시:

```bash
python main.py --ingest --pdf-dir ./pdf --with-scheduler
```

---

## 처음 보는 사람이 기억하면 좋은 점

- 이 코드는 UI보다 "지식 구축 + DB 적재" 성격이 강합니다.
- 데이터 저장소는 Neo4j입니다.
- 문서가 바뀌면 freshness 체크로 재검토 대상을 표시합니다.

---

## 추천 읽기 순서

1. main.py
2. db/graph_store.py
3. pipeline/extractor.py
4. pipeline/ingestor.py

이 순서로 보면 "데이터가 어떻게 쌓이고, 질문이 어떻게 답변으로 바뀌는지"를 가장 빠르게 이해할 수 있습니다.
