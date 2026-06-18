# Agent 패키지 구조 및 역할 정리

## 전체 처리 흐름

```
사용자 질문
    │
    ▼
[query_runner.py] run_query_loop()
    │
    ├─ 1. FAQ 빠른 매칭 ──────────────────► [faq.py] FastPathHandler.match()
    │        단순 질문이면 즉시 반환
    │
    ├─ 2. 언어/질문 유형 감지 ────────────► [agent_runtime.py] detect_language(), detect_question_type()
    │
    ├─ 3. Fast Path 검색 ─────────────────► [retrieval_engine.py] RetrievalEngine.retrieve()
    │        should_use_deep_path() 판단
    │
    ├─ 4. Deep Path (필요 시) ────────────► [agent_runtime.py] expand_query()
    │        변형 쿼리 추가 검색 + 결과 병합
    │        근거 여전히 부족 → 웹 크롤링
    │
    ├─ 5. 컨텍스트 조립 ─────────────────► [retrieval_engine.py] build_prompt_context()
    │
    ├─ 6. LLM 답변 생성 ─────────────────► [gemini_runtime_client.py] generate_answer()
    │                                        (또는 ollama_client.py)
    │
    └─ 7. 지연 로그 기록 ────────────────► [agent_runtime.py] append_latency_log()
```

---

## 파일별 상세 설명

---

### `__init__.py`

**역할:** `agent` 패키지의 진입점. 외부에서 사용할 함수를 공개(export)한다.

| 공개 함수 | 출처 파일 | 설명 |
|---|---|---|
| `run_ingest` | `ingest_runner.py` | PDF를 읽어 그래프 DB에 저장 |
| `run_embed_update` | `ingest_runner.py` | 기존 청크의 임베딩 일괄 갱신 |
| `run_query_loop` | `query_runner.py` | 대화형 질의응답 루프 실행 |

---

### `agent_runtime.py`

**역할:** 질문 분류, 경로 판단, 프롬프트 조립, 로그 기록 등 에이전트의 핵심 로직을 담당한다. 다른 모듈들이 이 파일의 함수를 호출해서 동작을 제어한다.

#### 주요 클래스/열거형

| 이름 | 설명 |
|---|---|
| `QuestionType` | 질문 유형 열거형: GENERAL / COMPARISON / CAUSE / EXCEPTION / DEADLINE / DOCUMENTS / APPLICATION |
| `GateThresholds` | fast→deep 전환 기준값. `min_top_score`(기본 0.25), `min_evidence_chunks`(기본 2). 환경변수로 조정 가능 |

#### 주요 함수

| 함수 | 역할 |
|---|---|
| `detect_language(text)` | 한글/한자 유니코드 범위로 언어 감지 → `"ko"` / `"zh"` / `"en"` 반환 |
| `normalize_query(text)` | 연속 공백을 하나로 줄이고 양끝 공백 제거. 검색 전 쿼리 정규화용 |
| `detect_question_type(text)` | 키워드 매칭으로 질문 유형 분류. 비교/원인/예외/기한/서류/신청 순으로 체크 |
| `expand_query(text, language)` | 원본 쿼리 + "비교/원인/예외" 계열 변형 쿼리 목록 생성. deep path에서 여러 각도로 검색할 때 사용 |
| `should_use_deep_path(query, top_score, evidence_count, thresholds)` | ① top 점수 미달 ② 근거 청크 수 미달 ③ 복잡한 질문 유형(COMPARISON/CAUSE/EXCEPTION) — 셋 중 하나라도 해당하면 deep path 필요로 판단. `(bool, 이유 목록)` 반환 |
| `run_fast_path(...)` | 쿼리 1개로 검색 1회 실행 후 `should_use_deep_path` 판단 결과 포함해 딕셔너리 반환 |
| `run_deep_path(...)` | 변형 쿼리 여러 개로 검색 반복 후 결과 병합. 여전히 근거 부족이면 `web_client.search_and_collect()`로 외부 보완 |
| `build_answer_prompt(...)` | LLM에 전달할 최종 프롬프트 문자열 조립 (헤더 + 출력형식 지시 + 사용자 프로파일 + 대화 이력 + 근거 컨텍스트 + 출처 목록 + 질문) |
| `append_latency_log(...)` | 처리 경로(fast/deep), 응답 시간, 검색 점수 등을 JSONL 파일에 한 줄씩 기록. 나중에 통계 분석용 |
| `insufficient_evidence_message(language)` | 근거 부족 시 사용자에게 보여줄 안내 메시지를 언어별로 반환 |
| `status_update_message(language, profile_text)` | 사용자 프로파일 업데이트 확인 메시지를 언어별로 반환 |

---

### `faq.py`

**역할:** 단순 반복 질문에 대한 FAQ 빠른 경로(fast path). 키워드 매칭으로 즉시 답변하여 LLM 호출 비용을 줄인다.

#### 주요 구성요소

| 이름 | 설명 |
|---|---|
| `_COMPLEX_INDICATORS` | "비교", "차이", "조건", "그리고" 등 복합 질문을 나타내는 키워드 목록 |
| `_is_complex_question(question)` | `_COMPLEX_INDICATORS` 중 하나라도 포함되면 True. 복합 질문은 FAQ를 건너뛰고 검색기로 넘긴다 |
| `_FAQ_DB` | `(키워드 목록, 답변)` 튜플의 리스트. D-4/D-2 비자, 비자 연장, 외국인등록, 건강보험 등 18개 항목 |
| `FastPathHandler.match(question)` | 복합 질문이면 `None` 반환. 단순 질문이면 `_FAQ_DB`에서 키워드 매칭 수가 가장 많은 답변 반환 |

#### 처리 규칙
- 복합 질문(`_is_complex_question` = True) → 무조건 `None` 반환, 검색기로 위임
- 키워드 매칭 수 ≥ 1인 항목 중 가장 많이 매칭된 답변 선택

---

### `gemini_runtime_client.py`

**역할:** 런타임 답변 생성용 Gemini LLM 클라이언트. 질문 정규화와 최종 답변 생성을 담당한다.

#### 주요 클래스: `GeminiRuntimeClient`

| 메서드 | 역할 |
|---|---|
| `__init__(model)` | Gemini API 설정 및 사용 가능한 모델 탐색. 설정된 모델이 지원 안 되면 자동 fallback |
| `_init_model_with_fallback(preferred_model)` | 선호 모델 → `gemini-1.5-flash` → `gemini-1.5-pro` 순서로 ping 테스트 후 첫 번째 성공한 모델 사용 |
| `is_available()` | 모델이 초기화됐으면 True |
| `_call(prompt, max_tokens, temperature, top_p)` | Gemini API 호출 후 텍스트 추출. quick accessor 실패 시 candidates 직접 조회하는 fallback 포함 |
| `normalize_question(question)` | `_NORMALIZE_PROMPT`를 사용해 비표준 표현("비자 늘리기" → "비자 연장")을 표준 용어로 변환 |
| `generate_answer(question, context, result, web_context)` | `_ANSWER_PROMPT_TEMPLATE` 또는 웹 컨텍스트용 템플릿으로 최종 답변 생성. 한국어 이외 스크립트 감지 시(`_has_forbidden_script`) 기본 응답으로 대체 |

#### 프롬프트 템플릿
| 템플릿 | 용도 |
|---|---|
| `_ANSWER_PROMPT_TEMPLATE` | DB 검색 결과만 사용할 때 |
| `_ANSWER_PROMPT_WEB_TEMPLATE` | 웹 검색 결과까지 포함할 때 (URL 명시 지시 추가) |
| `_NORMALIZE_PROMPT` | 질문의 비표준 표현을 표준 키워드로 변환 |

---

### `ollama_client.py`

**역할:** `gemini_runtime_client.py`와 동일한 인터페이스를 가진 로컬 LLM(Ollama/EXAONE 3.5 7B) 클라이언트. Gemini API를 사용할 수 없을 때 대안으로 사용한다.

#### 주요 클래스: `OllamaRuntimeClient`

| 메서드 | 역할 |
|---|---|
| `_call(prompt, system, max_tokens)` | Ollama `/api/generate` REST 엔드포인트 호출. 연결 실패 시 명확한 에러 로그 |
| `normalize_question(question)` | Gemini와 동일한 정규화 프롬프트 사용 |
| `generate_answer(question, context, result)` | DB 검색 결과 기반 답변 생성 (웹 컨텍스트 파라미터 없음 — Gemini와 시그니처 차이 존재) |
| `is_available()` | Ollama 서버 `/api/tags` 엔드포인트 ping으로 가용 여부 확인 |
| `close()` | requests 세션 정리 |

#### Gemini와의 차이점
- `generate_answer`에 `web_context` 파라미터 없음
- `retrieval_method == "no_answer"`일 때 즉시 기본 응답 반환
- 로컬 HTTP 연결이므로 네트워크 지연이 없지만 GPU 자원 필요

---

### `ingest_runner.py`

**역할:** 데이터 파이프라인 진입점. PDF 파일을 읽어 처리하고 그래프 DB에 저장하는 일괄 처리 작업을 수행한다. 서비스 실행과는 별개로 데이터 구축 단계에서 사용한다.

#### 주요 함수

| 함수 | 역할 |
|---|---|
| `run_ingest(pdf_dir, use_llm)` | PDF 디렉토리 순회 → 텍스트 로드 → 클리닝 → 청킹 → 임베딩 생성 → 개체/관계 추출 → 그래프 DB 저장 |
| `run_embed_update()` | 기존 그래프 DB의 청크 중 임베딩이 없는 것만 골라 배치로 임베딩 생성 후 upsert |

#### `run_ingest` 내부 파이프라인

```
PDFLoader.load(pdf_path)
    → clean_text()          # 텍스트 정제
    → chunk_document()      # 청크 분할
    → Embedder.encode()     # 벡터 임베딩 생성
    → HybridExtractor.extract_all()   # 개체/관계/청크 링크 추출
    → GraphIngestor.ingest_all()      # 그래프 DB 저장
```

---

### `retrieval_engine.py`

**역할:** 그래프 검색과 벡터 검색을 함께 실행하고 결과를 병합·재정렬하는 검색 오케스트레이터. `query_runner.py`가 직접 호출하는 핵심 검색 모듈이다.

#### 주요 클래스: `RetrievalEngine`

| 메서드 | 역할 |
|---|---|
| `__init__(store, embedder, ollama_client)` | `EntityLinker`, `DDEGraphRetriever`, `VectorRetriever` 초기화 |
| `retrieve(question, hop_depth, top_k)` | 주 검색 메서드. 아래 4단계를 순서대로 실행 |
| `_merge_and_rerank(graph_chunks, vector_chunks, question, anchors)` | 그래프+벡터 청크를 합산 점수로 병합·재정렬 |
| `build_prompt_context(result)` | 검색 결과를 LLM 프롬프트용 컨텍스트 문자열로 변환 |
| `invalidate_caches()` | 인제스트 후 내부 캐시(링커 + 벡터 인덱스) 무효화 |

#### `retrieve()` 4단계 흐름

```
1. EntityLinker.link(question)
   → entity_ids, anchors, intents 추출

2. DDEGraphRetriever.retrieve(entity_ids)
   → 그래프 탐색으로 관련 triple + chunk 수집

3. VectorRetriever.search(question)
   → 그래프 결과가 부족하거나 다중 의도일 때만 실행

4. _merge_and_rerank()
   → 합산 점수 = 0.6*base + 0.3*keyword_overlap + 0.1*recency
   → 점수 0.30 미만 제거 → 상위 4개 반환
```

#### 점수 체계

| 가중치 | 의미 |
|---|---|
| `_W_BASE = 0.60` | 기본 점수 (그래프: 0.75 고정 / 벡터: cosine 유사도) |
| `_W_KW = 0.30` | 앵커 키워드 및 질문 단어 겹침 |
| `_W_REC = 0.10` | 문서 최신성 (24개월 기준 선형 감소) |
| `_MIN_CHUNK_SCORE = 0.30` | 이 미만 청크는 결과에서 제외 |
| `_QUESTION_FIT_THRESHOLD = 0.06` | 질문-문서 적합도가 이 미만이면 `no_answer` 처리 |

---

### `query_runner.py`

**역할:** 전체 질의응답 루프를 실행하는 메인 컨트롤러. 위의 모든 모듈을 조합해 사용자 입력을 처리한다.

#### 주요 함수

| 함수 | 역할 |
|---|---|
| `run_query_loop()` | 대화형 루프 실행. 종료 키워드("quit"/"exit") 입력까지 반복 |
| `_merge_results(base, extras)` | 여러 `RetrievalResult`를 병합. 같은 chunk_id가 여러 번 나오면 가장 높은 점수만 유지. 상위 4개 반환 |

#### `run_query_loop()` 처리 단계

| 단계 | 설명 | 관련 모듈 |
|---|---|---|
| 1. FAQ 빠른 매칭 | 단순 질문이면 즉시 반환, 복합 질문이면 통과 | `faq.py` |
| 2. 언어/유형 감지 | 언어 코드와 QuestionType 결정 | `agent_runtime.py` |
| 3. Fast Path 검색 | 단일 쿼리로 검색 후 deep 여부 판단 | `retrieval_engine.py`, `agent_runtime.py` |
| 4. Deep Path (조건부) | 변형 쿼리로 추가 검색 + `_merge_results()` | `agent_runtime.py` |
| 5. 웹 검색 (조건부) | deep path 후에도 근거 부족이면 웹 크롤링 | `WebSearchClient` |
| 6. 컨텍스트 조립 | 검색 결과 + 웹 결과 합산 | `retrieval_engine.py` |
| 7. LLM 답변 생성 | Gemini로 최종 답변. LLM 없으면 컨텍스트 직접 출력 | `gemini_runtime_client.py` |
| 8. 지연 로그 기록 | `logs/latency.jsonl`에 처리 정보 기록 | `agent_runtime.py` |

---

## 파일 간 의존 관계

```
__init__.py
├── ingest_runner.py          (데이터 구축)
└── query_runner.py           (서비스 실행)
        │
        ├── agent_runtime.py           (질문 분류 · 경로 판단 · 프롬프트)
        ├── faq.py                     (빠른 FAQ 매칭)
        ├── gemini_runtime_client.py   (LLM 호출)
        ├── retrieval_engine.py        (그래프+벡터 검색)
        │       ├── retrieval/graph_retriever.py
        │       ├── retrieval/vector_retriever.py
        │       └── retrieval/linker.py
        └── crawler/web_search_client.py  (웹 검색 fallback)
```

## 모듈 역할 요약

| 파일 | 레이어 | 한 줄 요약 |
|---|---|---|
| `__init__.py` | 진입점 | 패키지 공개 함수 정의 |
| `agent_runtime.py` | 제어 로직 | 질문 분류, 경로 판단, 프롬프트 조립 |
| `faq.py` | 빠른 경로 | 키워드 기반 FAQ 즉시 응답 |
| `gemini_runtime_client.py` | LLM | Gemini API로 답변 생성 |
| `ollama_client.py` | LLM (대안) | 로컬 Ollama로 답변 생성 |
| `ingest_runner.py` | 데이터 파이프라인 | PDF → 그래프 DB 저장 |
| `retrieval_engine.py` | 검색 | 그래프+벡터 검색 병합·재정렬 |
| `query_runner.py` | 오케스트레이터 | 전체 질의응답 루프 통합 실행 |
