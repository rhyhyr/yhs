# YHS 프로젝트 인수인계 문서

동아대학교 외국인 유학생 지원 AI 챗봇 — 졸업 작품

---

## 프로젝트 개요

외국인 유학생이 비자 연장, 외국인등록증, 건강보험 가입, 학사 일정 등 유학 생활에서 겪는 행정·생활 정보를 한국어/영어/중국어로 질의응답할 수 있도록 만든 AI 챗봇이다.

단순 키워드 검색이 아니라 **Graph RAG(Retrieval-Augmented Generation)** 구조를 사용한다. PDF 문서에서 추출한 개념(엔티티)과 관계(트리플)를 Neo4j 그래프 데이터베이스에 저장한 뒤, 사용자 질문에 맞는 노드를 탐색(그래프 검색)하고 임베딩 유사도 검색(벡터 검색)과 합산해 근거 문서를 추린다. 최종 답변은 Gemini LLM이 생성한다.

---

## 전체 아키텍처

```
pdf/                        ← 원본 PDF 문서 (입력)
  └─ *.pdf

graph_rag/                  ← 핵심 RAG 엔진 (인제스트 + DB + 검색 기반)
  ├─ config.py              ← 모든 설정값 (Neo4j URI, 모델명, 임계값 등)
  ├─ schema/types.py        ← 데이터 모델 정의 (ChunkNode, EntityNode, Triple…)
  ├─ db/graph_store.py      ← Neo4j 연결 및 CRUD
  ├─ embedding/embedder.py  ← 임베딩 모델 (BAAI/bge-m3, sentence-transformers)
  ├─ pipeline/              ← PDF → 그래프 DB 인제스트 파이프라인
  │   ├─ loader.py          ← PDF 텍스트 추출 (pdfplumber)
  │   ├─ cleaner.py         ← 텍스트 정제
  │   ├─ chunker.py         ← 청크 분할 (512 토큰 단위)
  │   ├─ extractor.py       ← 엔티티·관계 추출 (규칙 기반 + LLM)
  │   └─ ingestor.py        ← 추출 결과 → Neo4j 적재
  ├─ llm/                   ← LLM 클라이언트 (인제스트용)
  │   ├─ gemini_client.py
  │   └─ openai_client.py
  ├─ fast_path/             ← 간단 쿼리 빠른 경로
  └─ scheduler/freshness.py ← 6개월 이상 경과 문서 갱신 알림

agent/                      ← 질의응답 에이전트 (런타임)
  ├─ query_runner.py        ← 대화 루프 (main 진입점)
  ├─ agent_runtime.py       ← 언어 감지, Fast/Deep Path 판단, 프롬프트 조립
  ├─ retrieval_engine.py    ← 검색 오케스트레이터 (그래프 + 벡터 병합)
  ├─ retrieval/
  │   ├─ linker.py          ← 질문 → 그래프 Entity 링킹
  │   ├─ graph_retriever.py ← DDE 멀티홉 그래프 탐색
  │   └─ vector_retriever.py← 벡터(임베딩) 검색
  ├─ gemini_runtime_client.py ← Gemini 답변 생성 클라이언트
  ├─ faq.py                 ← FAQ 즉답 처리
  ├─ ingest_runner.py       ← 인제스트 실행 진입점
  ├─ ollama_client.py       ← Ollama 로컬 LLM (선택)
  └─ crawler/
      └─ web_search_client.py ← 근거 부족 시 웹 검색 fallback

main.py                     ← python main.py 로 질의 루프 실행
```

---

## 환경 설정

### 1. Neo4j 설치

이 프로젝트는 **Neo4j 5.11 이상**이 필요하다 (네이티브 벡터 인덱스 기능 때문).

1. [https://neo4j.com/download/](https://neo4j.com/download/) 에서 **Neo4j Desktop** 또는 **Community Edition** 다운로드
2. 설치 후 데이터베이스를 생성하고 **DBMS를 시작(Start)**
3. 기본 포트: `bolt://localhost:7687`, 기본 DB 이름: `neo4j`
4. 비밀번호를 설정한 뒤 `.env`에 기입 (아래 참고)

> Neo4j Desktop을 사용하면 GUI에서 DB를 켜고 끌 수 있어 편하다. 코드 실행 전 반드시 Neo4j가 먼저 실행 중이어야 한다.

---

### 2. `.env` 파일 설정

프로젝트 루트의 `.env` 파일에 아래 키를 채워야 한다. 이 파일은 `.gitignore`에 포함되어 있으므로 Git에는 올라가지 않는다.

```env
# LLM API 키
GEMINI_API_KEY=<Google AI Studio에서 발급>
GEMINI_MODEL=gemini-3.0-flash

OPENAI_API_KEY=<OpenAI에서 발급 — 인제스트 시 엔티티 추출에 사용>

# Neo4j 연결 정보
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<설치 시 설정한 비밀번호>

# PDF 경로 (기본값은 프로젝트 루트의 pdf/ 폴더)
PDF_DIR=C:\Users\<사용자명>\...\yhs\pdf

# 인덱싱/쿼리 튜닝 (기본값 그대로 써도 됨)
CHUNK_SIZE=380
CHUNK_OVERLAP=76
SIM_THRESHOLD=0.27
TOP_K_VECTOR=5
MIN_CHUNKS_FOR_ANSWER=2
MIN_BEST_SCORE=0.40
```

`graph_rag/config.py`가 시작 시 `.env`를 자동으로 읽는다. python-dotenv 패키지 없이 자체 파싱한다.

---

### 3. 가상환경 생성

```bash
# 프로젝트 루트에서 실행
python -m venv .venv

# 활성화 (Windows)
.venv\Scripts\activate

# 활성화 (Mac/Linux)
source .venv/bin/activate
```

---

### 4. `install_windows.bat` 실행

가상환경을 활성화한 상태에서 실행한다.

```bash
install_windows.bat
```

이 파일이 하는 일:
1. pip/setuptools/wheel 최신화
2. 기존 torch 제거 (충돌 방지)
3. PyTorch 2.3.1 CPU 전용 버전 설치 (GPU 없이 실행할 수 있도록)
4. sentence-transformers 3.0.1 설치 (임베딩 모델)
5. neo4j 드라이버 5.20.0 설치
6. google-generativeai, pdfplumber, numpy, scikit-learn 설치

> **왜 별도 bat 파일인가?** PyTorch는 Windows에서 requirements.txt 한 번에 설치하면 버전 충돌이 잦다. CPU 전용 wheel URL을 명시해서 설치하기 위해 분리해 두었다.

---

### 5. 나머지 패키지 설치

```bash
pip install -r requirements.txt
```

주요 패키지: `neo4j`, `google-generativeai`, `pdfplumber`, `sentence-transformers`, `requests`, `beautifulsoup4`, `faiss-cpu`, `openai`, `langchain-*`

---

## 실행 방법

### 인제스트 (PDF → 그래프 DB 적재)

```bash
python -m agent ingest
```

또는 코드에서:

```python
from agent import run_ingest
from pathlib import Path
run_ingest(Path("pdf/"))
```

처음 실행하거나 새 PDF를 추가했을 때 실행한다. 시간이 오래 걸릴 수 있다 (임베딩 생성 + LLM 엔티티 추출).

### 질의 루프 실행

```bash
python main.py
```

터미널에서 대화형으로 질문을 입력한다. `quit` 또는 `exit`로 종료.

---

## 질의 처리 실행 흐름

```
사용자 입력
    │
    ▼
[1] FAQ 빠른 매칭 (faq.py)
    - 단순 비자 설명 등 즉답 가능한 질문은 여기서 바로 반환
    - 복합/조건부/비교 질문은 스킵
    │
    ▼ (FAQ 미스 시)
[2] 언어 감지 + 질문 유형 분류 (agent_runtime.py)
    - 한국어 / 영어 / 중국어 감지
    - GENERAL / COMPARISON / CAUSE / EXCEPTION / DEADLINE / DOCUMENTS / APPLICATION
    │
    ▼
[3] Fast Path — 단일 검색 (retrieval_engine.py)
    │
    ├─ EntityLinker: 질문 → 그래프 Entity ID 매핑 (linker.py)
    │     의도 분류(비자/외국인등록/건강보험…) → aliases 매칭 + 임베딩 유사도
    │
    ├─ DDEGraphRetriever: Entity 노드 → 멀티홉 탐색 (graph_retriever.py)
    │     홉 0=1.0 / 홉 1=0.5 / 홉 2=0.25 스코어 → 연결 Chunk 수집
    │
    └─ VectorRetriever: 질문 임베딩 → Neo4j 벡터 인덱스 검색 (vector_retriever.py)
          hybrid_score = 0.65 * cosine + 0.25 * keyword_overlap + 0.10 * recency
    │
    ▼
[4] should_use_deep_path() 판정
    - top_score < 0.25  → "low_top_score"
    - chunk 수 < 2      → "insufficient_evidence"
    - 비교/원인/예외 질문 → "complex_question"
    셋 중 하나라도 해당하면 Deep Path 진입
    │
    ▼ (Deep Path 진입 시)
[5] Deep Path (query_runner.py)
    - expand_query()로 변형 쿼리 3개 생성 ("비교 차이", "원인 이유", "예외 제외")
    - 각 변형 쿼리로 추가 검색 → 결과 병합 (chunk_id 기준 최고 점수 유지)
    - 병합 후에도 근거 부족하면 웹 검색 fallback (WebSearchClient)
    │
    ▼
[6] 컨텍스트 조합
    - 그래프 트리플 + 원문 청크 + 출처 메타데이터 + (웹 결과)
    - 6개월 이상 경과 문서는 자동으로 면책 문구 삽입
    │
    ▼
[7] LLM 답변 생성 (gemini_runtime_client.py)
    - Gemini에 엄격한 규칙 프롬프트 + 근거 문서 + 질문 전달
    - 근거 없으면 "제공된 자료에서는 확인할 수 없습니다" 고정 문구 반환
    │
    ▼
[8] 레이턴시 로그 기록 (logs/latency.jsonl)
    - ts, path(fast/deep), elapsed_sec, best_score, evidence_count
```

---

## 주요 모듈 상세

### `graph_rag/config.py`
모든 설정의 단일 진입점. `.env`를 읽어 환경변수를 채운 뒤 상수로 노출한다. 임계값이나 모델명을 바꿀 때 여기를 수정하거나 `.env`에서 오버라이드한다.

### `graph_rag/db/graph_store.py`
Neo4j 연결을 관리한다. Context manager(`with GraphStore() as store`)로 사용한다. 스키마 초기화(제약·인덱스), 노드/엣지 upsert, 네이티브 벡터 인덱스 검색, confidence 낮은 트리플 격리(`review_queue.json`)를 담당한다.

### `graph_rag/pipeline/extractor.py`
규칙 기반(정규식으로 비자코드·기관명 추출, confidence=1.0)과 LLM 기반(OpenAI로 구조화 JSON 추출, confidence=0.7~0.9)을 합친 하이브리드 추출기. 허용 predicate는 `ALLOWED_PREDICATES` 7개로 고정되어 있다.

### `agent/retrieval_engine.py`
그래프 검색과 벡터 검색 결과를 합산 스코어로 재정렬하는 오케스트레이터.
- `_W_BASE * base_score + _W_KW * keyword_overlap + _W_REC * recency`
- 같은 Chunk가 양쪽에서 나오면 더 높은 점수를 사용한다.

### `agent/agent_runtime.py`
언어 감지, 질문 유형 분류, Fast/Deep 경로 판정, LLM 프롬프트 조립 함수 모음. 로직만 있고 I/O는 없어서 단독으로 테스트하기 쉽다.

### `graph_rag/schema/types.py`
모든 레이어가 공유하는 데이터 모델. DB 레이어와 파이프라인 레이어 사이의 계약이다. 새 노드 타입이나 엣지 타입을 추가할 때 여기에 먼저 추가한다.

---

## 데이터 흐름 요약

```
PDF 파일
  ↓ PDFLoader (pdfplumber)
RawDocument (text, source_file, page, doc_version)
  ↓ cleaner → chunker
ChunkNode[] (512토큰 단위, overlap 76)
  ↓ Embedder (BAAI/bge-m3, 1024차원)
ChunkNode[].embedding
  ↓ HybridExtractor
EntityNode[], Triple[], chunk_links[]
  ↓ GraphIngestor
Neo4j DB
  - :Chunk 노드 (embedding 포함)
  - :Entity 노드
  - [:FOUND_IN] 엣지 (Entity → Chunk)
  - [:CAN_TRANSITION_TO | REQUIRES | BLOCKS …] 관계 트리플
```

---

## 자주 바꾸게 될 설정값

| 설정 | 파일 | 의미 |
|------|------|------|
| `CONFIDENCE_THRESHOLD` | config.py / .env | 이 값 미만 트리플은 review_queue로 격리 (기본 0.7) |
| `GATE_MIN_TOP_SCORE` | .env | Fast→Deep 전환 임계값 (기본 0.25) |
| `GATE_MIN_EVIDENCE` | .env | 최소 근거 청크 수 (기본 2) |
| `MAX_CHUNK_TOKENS` | config.py / .env | 청크 최대 토큰 수 (기본 512) |
| `DEFAULT_HOP_DEPTH` | config.py / .env | 그래프 탐색 홉 깊이 (기본 2) |
| `EMBEDDING_MODEL` | config.py / .env | 임베딩 모델명 |
| `GEMINI_MODEL` | .env | Gemini 모델 버전 |

---

## 주의사항

- **Neo4j는 코드 실행 전에 반드시 먼저 켜야 한다.** `graph_store.py`가 연결에 실패하면 시작 시 에러가 난다.
- `.env` 파일을 Git에 올리지 않도록 주의. API 키가 포함되어 있다.
- 인제스트를 다시 실행하면 기존 데이터에 upsert(merge)된다. 완전 초기화가 필요하면 Neo4j에서 DB를 직접 비워야 한다.
- `install_windows.bat`은 **가상환경이 활성화된 상태**에서 실행해야 한다. 활성화 없이 실행하면 전역 Python에 설치된다.
- `logs/latency.jsonl`에 모든 질의 처리 시간이 기록된다. 운영 중 slow query를 확인할 때 참고한다.
