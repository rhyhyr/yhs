# 모듈 구조

`backend/src/yhs/` 의 파일별 역할. 큰 그림과 튜닝 지점은 [HANDOVER](HANDOVER.md)에 있다.

> 2026-09-14 구조 개편으로 `agent/`, `graph_rag/` 두 패키지가 `yhs` 하나로 합쳐졌다.
> 옛 경로를 참조하는 문서·노트가 남아 있다면 아래 표로 대응시킨다.
>
> | 옛 경로 | 현재 |
> |---|---|
> | `agent/agent_runtime.py` | `rag/runtime.py` |
> | `agent/retrieval_engine.py` | `rag/engine.py` |
> | `agent/gemini_runtime_client.py` | `rag/llm/gemini_client.py` |
> | `agent/ollama_client.py` | `rag/llm/ollama_client.py` |
> | `agent/ingest_runner.py` | `ingest/runner.py` |
> | `graph_rag/db/graph_store.py` | `infra/graph_store.py` |
> | `graph_rag/embedding/embedder.py` | `infra/embedder.py` |
> | `graph_rag/scheduler/freshness.py` | `infra/freshness.py` |
> | `graph_rag/pipeline/` | `ingest/pipeline/` |

---

## core — 설정

### `settings.py`

두 가지를 제공한다.

- `Settings` — 환경변수와 `.env` 를 읽는 pydantic-settings 모델. 비밀키, 접속 주소,
  경로, 실행 모드가 여기 있다. `.env` 는 저장소 루트와 cwd 순으로 찾는다.
- `load_config(name)` — `backend/config/<name>.yaml` 을 dict 로 읽는다.
  `functools.cache` 가 걸려 있어 프로세스당 한 번만 읽는다.

설정 디렉토리는 소스 트리면 `backend/config/`, 설치본이면 휠에 동봉된
`yhs/_config/` 를 쓴다 (`pyproject.toml` 의 `force-include`).

`_override(yaml_value, env_value)` — 같은 항목이 양쪽에 있으면 환경변수가 이긴다.
테스트·실험에서 값을 바꿔 가며 쓸 때는 `reload_config()` 로 캐시를 비운다.

### `config.py`

`Settings` 와 YAML 을 합쳐 대문자 상수로 노출하는 평면 뷰. 구조 개편 전 코드가
`from yhs.core.config import TOP_K_VECTOR` 처럼 쓰던 것을 그대로 쓰게 한다.

**값이 import 시점에 고정된다.** 새 코드는 `get_settings()` / `load_config()` 를
직접 쓰는 편이 낫다.

---

## schema — 데이터 계약

`types.py` 하나. `ChunkNode`, `EntityNode`, `Triple`, `RetrievalResult`.
`ingest` 와 `rag` 가 공유하므로, 노드·엣지 타입을 추가할 때 여기부터 손댄다.

---

## infra — 외부 시스템 어댑터

| 파일 | 역할 |
|---|---|
| `graph_store.py` | Neo4j 연결·Cypher·네이티브 벡터 인덱스. context manager 로 쓴다 |
| `embedder.py` | BAAI/bge-m3 (1024차원) 임베딩 생성, 코사인 유사도 |
| `freshness.py` | **빈 스텁.** 신선도 관리는 `rag/crawler/` 로 이전됐다 |

---

## ingest — 지식베이스 구축

### `pipeline/`

```
loader.py    PDF → 페이지 텍스트 (pdfplumber)
cleaner.py   머리말·꼬리말 등 잡음 제거
chunker.py   페이지 경계를 넘어 이어 붙여 청크 생성
extractor.py 규칙 기반 + LLM 추출 병합
ingestor.py  정규 id 생성 후 Neo4j 적재
```

**`extractor.py`** — `HybridExtractor.extract_all()` 이 규칙 추출과 LLM 추출을
합친다. 규칙은 비자코드 정규식과 기관명만 잡으므로 *보장용*, LLM 이 *확장용*이다.
`_dedupe_entities()` 가 id 기준으로 중복을 제거하되, 같은 id 면 confidence 높은 쪽을
남기고 빈 필드는 다른 쪽에서 채운다. 규칙은 type 을 모르고 LLM 은 알기 때문이다.

`normalize_predicate()` 가 같은 뜻의 변형을 표준 술어로 모은다
(`NEEDS`/`DEPENDS_ON` → `REQUIRES`, `NEXT_STEP` → `PRECEDES` 등).
허용 밖 술어는 조용히 버리지 않고 건수를 집계한다.

**`ingestor.py`** — `GraphIngestor.ingest_triples()` 는 관계를 쓰기 전에 적재된
엔티티 id 집합과 대조한다. `upsert_triple` 이 양 끝을 MATCH 로 찾는데 없으면
0행이 되고 MERGE 가 실행되지 않으며, 예외도 나지 않는다. 미리 걸러 경고를 남긴다.

엔티티 id 는 **LLM 이 준 값을 쓰지 않고 이름에서 만든다.** 이름이 같은 엔티티는
한 노드로 합쳐진다.

### `llm/`

| 파일 | 내용 |
|---|---|
| `prompts.py` | 추출 프롬프트 한 벌. 모든 provider 공용 |
| `openai_client.py` | OpenAI. `strict: true` json_schema 로 타입·술어를 디코딩 단계에서 고정 |
| `exaone_kb_client.py` | 로컬 HuggingFace. 기본 모델은 `Qwen/Qwen2.5-7B-Instruct` (파일명과 다름) |
| `gemini_client.py` | Gemini |
| `ollama_kb_client.py` | Ollama |

프롬프트의 타입·술어 enum 은 `validation.py` 에서 직접 가져온다. 프롬프트 표와
검증 표가 어긋날 수 없게 하기 위해서다.

### `validation.py`

그래프에 넣기 전 검사. 주요 상수:

| 이름 | 내용 |
|---|---|
| `ENTITY_TYPES` | 7종 — PROCEDURE, DOCUMENT, CONDITION, VISA, PERSON_GROUP, ORGANIZATION, PRODUCT |
| `PREDICATE_TYPES` | 술어별로 허용되는 (subject 타입, object 타입) 조합 |
| `CHUNK_TYPES` / `DESCRIPTIVE_CHUNK_TYPES` | 문단 유형. 설명성 문단에서는 절차 관계를 막는다 |
| `DROP_UNUSED_ORG_IN_DESCRIPTIVE` | 설명성·목록 문단에서 나왔고 관계가 없는 ORGANIZATION 을 노드로 만들지 않는다 |
| `_MAX_NAME_LEN` = 75 | 이름 길이 상한. 문장 판별은 어절 수·영어 기능어·소문자 시작으로 따로 한다 |

`validate()` 에 `trace` 파라미터가 있다. 분석용 로직을 따로 짜면 실제 적재와
어긋나므로 함수는 하나만 두고 관찰만 덧붙였다. 적재 경로는 `trace` 를 넘기지 않는다.

### `stats.py`, `runner.py`

`stats.py` 는 인제스트 1회분을 집계한다 — `llm_failed_chunks`, `dropped_entities`,
`predicate_rejected`, `relation_match_failed` 등과 실패 사유·샘플. 조용한 실패를
드러내는 장치라 인제스트 끝에 반드시 출력된다.

`runner.py` 의 `run_ingest()` 는 추출부터 적재까지 한 번에 도는 옛 진입점
(`yhs --ingest`). `run_embed_update()` 는 임베딩이 없는 청크만 골라 채운다.

---

## rag — 질의 응답

### `faq.py`

`faq.yaml` 을 읽어 `(키워드 목록, 답변)` 으로 만든다.
`_is_complex_question()` 이 `complex_indicators` 중 하나라도 잡으면 무조건 `None` 을
반환하고 검색기로 넘긴다 — 복합·조건부·시점 의존 질문에 정적 답변은 위험하다.
매칭은 키워드 일치 수가 가장 많은 항목을 고른다.

### `runtime.py`

I/O 없이 로직만 있어 단독 테스트가 쉽다.

| 이름 | 역할 |
|---|---|
| `QuestionType` | GENERAL / COMPARISON / CAUSE / EXCEPTION / DEADLINE / DOCUMENTS / APPLICATION |
| `GateThresholds.from_config()` | `retrieval.yaml` 의 `gate` 섹션을 읽는다. 환경변수가 있으면 그쪽이 이긴다 |
| `detect_language()` | 한글·한자 유니코드 범위로 `ko`/`zh`/`en` 판별 |
| `detect_question_type()` | 키워드 매칭으로 질문 유형 분류 |
| `expand_query()` | deep path 용 변형 쿼리 목록 생성 |
| `should_use_deep_path()` | ① 점수 미달 ② 근거 수 미달 ③ 복합 유형 — 하나라도 걸리면 deep. `(bool, 이유)` 반환 |
| `build_answer_prompt()` | 최종 프롬프트 조립 |
| `append_latency_log()` | 경로·소요시간·점수를 JSONL 로 기록 |

`GateThresholds` 의 dataclass 기본값(0.17)은 폴백일 뿐이다. 실효값은
`retrieval.yaml` 의 `gate.min_top_score`.

### `engine.py` — 검색 오케스트레이터

`RetrievalEngine.retrieve()` 의 순서:

```
1. EntityLinker.link()            질문 → entity_ids, anchors
2. DDEGraphRetriever.retrieve()   그래프 탐색 → triples, chunks
3. VectorRetriever.search()       임베딩 검색 (그래프와 항상 병행)
4. _fetch_source_routed_chunks()  routing.yaml 키워드 → 소스 파일 강제 포함
5. _merge_and_rerank()            합산 점수로 재랭크
```

재랭크 점수는 `_W_BASE × base + _W_KW × keyword + _W_REC × recency`.
세 가중치와 문턱값은 전부 `retrieval.yaml` 에서 온다 — 코드에 숫자를 박지 않는다.

`_apply_routed_quota()` 가 라우팅된 청크에 최소 자리를 확보한다
(`rerank.routed_min_slots`). `_is_header_chunk()` 는 `URL:`, `출처기관:` 만 있는
메타 청크에 페널티를 준다. `_dedupe_by_text()` 는 같은 본문이 여러 청크로
잡히는 것을 정리한다.

`build_prompt_context()` 가 검색 결과를 LLM 프롬프트용 문자열로 바꾼다.
`doc_staleness_months`(기본 6) 를 넘긴 문서에는 면책 문구가 붙는다.

### `retrieval/`

| 파일 | 역할 |
|---|---|
| `linker.py` | 질문 → Entity id. LLM 정규화 → 별칭 매칭 → 임베딩 매칭 순. 임계값 `entity_link.cosine_threshold` |
| `graph_retriever.py` | BFS 멀티홉. 홉마다 점수 감쇠(`dde_score_by_hop`), `RELATED_TO` 는 탐색 제외 |
| `vector_retriever.py` | 임베딩 top-k 후보 수집. 반환 `score` 는 **순수 코사인**이고, 키워드·최신성을 섞은 최종 점수는 `engine.py` 가 계산한다 |
| `translator.py` | 중국어 질문을 `Helsinki-NLP/opus-mt-zh-ko` 로 번역. 결과는 메모리 캐시 |

### `llm/`

`openai_client.py`, `gemini_client.py`, `ollama_client.py`, `hf_client.py`.
`.env` 의 `RUNTIME_LLM` 으로 고른다 (인제스트용 `LLM_PROVIDER` 와 별개).

### `crawler/`

근거가 부족할 때의 웹 폴백. `web_search_client.py` 가 검색·리다이렉트 해제·
허용 도메인 필터링·본문 추출을 담당한다. 허용 도메인과 크롤 예산은
`crawler.yaml` 에 있다.

### `query_runner.py`

터미널 질의 루프(`yhs --query`). `process_question()` 이 FAQ → 검색 → deep path →
웹 폴백 → LLM 순서를 엮고, `run_query_loop()` 이 그걸 `input()` 루프로 감싼다.

### `feature_flags.py`, `ab_test.py`

환경변수 기반 기능 토글과 해시 기반 A/B 배정. 이벤트는 `logs/ab_events.jsonl` 로 쌓인다.

---

## api — FastAPI

| 파일 | 역할 |
|---|---|
| `main.py` | 앱 생성, lifespan 에서 `AppState` 구성 |
| `deps.py` | `AppState` — GraphStore·Embedder·RetrievalEngine·LLM 을 한 번만 만들어 들고 있다. `build_llm()` 이 `RUNTIME_LLM` 을 보고 클라이언트를 고른다 |
| `service.py` | `answer_question()` — 질문 하나 → 답변 + 근거. 파일명을 사람이 읽을 라벨로 바꾸는 `_pretty_label()` 포함 |
| `routes/chat.py` | `POST /api/chat`, `POST /query`(deprecated) |
| `routes/health.py` | `GET /health` |
| `schemas.py` | 요청·응답 모델 |

`query_runner.py` 와 `service.py` 는 같은 `RetrievalEngine` 을 쓰는 별개 진입점이다.
검색 동작을 바꾸면 양쪽에 같이 반영된다.
