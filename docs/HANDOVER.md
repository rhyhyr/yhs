# 인수인계

동아대학교 외국인 유학생 지원 AI 챗봇. Graph RAG 구조다.

설치·실행·API 명세는 [README](../README.md)에 있다. 이 문서는 그 다음 —
**코드가 어떻게 생겼고, 무엇을 고치면 무엇이 바뀌는가**를 다룬다.

---

## 1. 전체 구조

두 개의 독립된 파이프라인이 Neo4j 하나를 공유한다.

```
[구축]  PDF 35종 ──► 청크 ──► 엔티티·관계 ──► Neo4j
                                              │
[질의]  질문 ──► 그래프 탐색 + 벡터 검색 ──┘──► 재랭크 ──► LLM ──► 답변
```

구축은 가끔 돌리는 배치고, 질의는 상시 서비스다. 둘은 코드도 분리돼 있다
(`ingest/` ↔ `rag/`). 공유하는 건 Neo4j와 `schema/types.py`의 데이터 계약뿐이다.

### 패키지 배치

```
backend/src/yhs/
├── core/       설정 단일 진입점
│   ├── settings.py   환경변수·.env (pydantic-settings) + YAML 로더
│   └── config.py     위 둘을 합친 대문자 상수 평면 뷰 (레거시 호환)
├── schema/types.py   ChunkNode, EntityNode, Triple, RetrievalResult
├── infra/            외부 시스템 어댑터
│   ├── graph_store.py  Neo4j 연결·Cypher·벡터 인덱스
│   └── embedder.py     BAAI/bge-m3 (1024차원)
├── ingest/           지식베이스 구축
├── rag/              질의 응답
└── api/              FastAPI (routes / schemas / service / deps)
```

`core/config.py`의 값은 **import 시점에 고정된다.** 런타임에 환경변수를 바꿔도
반영되지 않으니, 새 코드는 `get_settings()` / `load_config()` 를 직접 쓰는 편이 낫다.

---

## 2. 지식베이스 구축 (`ingest/`)

### 3단계로 쪼개져 있다

한 덩어리였을 때는 검증 규칙을 한 줄 고칠 때마다 147청크를 다시 호출해야 했다.
지금은 이렇다:

```
scripts/kb_extract.py   LLM 호출 → data/extract/raw.jsonl     API 비용 발생
scripts/kb_analyze.py   파싱·검증 재적용 + 전수 분석          API 호출 없음
scripts/kb_load.py      검증 통과분만 Neo4j 적재              API 호출 없음
```

추출 캐시 키는 `(chunk_id, model, prompt_version, schema_hash)` 다.
프롬프트를 고쳐 `PROMPT_VERSION` 을 올리면 영향받은 청크만 다시 부른다.

`data/extract/raw.jsonl` 은 **git 에 커밋돼 있다.** API 비용이 든 산출물이라,
추가 비용 없이 같은 지식베이스를 재현할 수 있다.

> `yhs --ingest` ([ingest/runner.py](../backend/src/yhs/ingest/runner.py))도 남아 있다.
> 추출부터 적재까지 한 번에 돌리는 옛 경로다. 최종 적재는 위 3단계로 했다.

### 파이프라인 내부

```
loader.py    PDF → 페이지 텍스트 (pdfplumber)
cleaner.py   머리말·꼬리말 등 잡음 제거
chunker.py   페이지 경계를 넘어 이어 붙여 청크 생성 (상한 512토큰)
extractor.py 규칙 기반 + LLM 추출을 합침
validation.py 그래프에 넣기 전 검사      ← 여기가 채택률을 결정한다
ingestor.py  이름에서 정규 id 생성 후 Neo4j 적재
```

`llm/prompts.py` 에 프롬프트가 **한 벌만** 있다. 타입·술어 enum 은 `validation.py`
에서 직접 가져오므로 프롬프트 표와 검증 표가 어긋날 수 없다. provider 마다
프롬프트를 따로 두던 시절 `openai_client.py` 만 옛 스키마에 멈춰 있던 적이 있다.

### 검증이 막는 5가지 — [validation.py](../backend/src/yhs/ingest/validation.py)

1. **endpoint 누락** — 관계의 양 끝이 같은 응답의 엔티티 목록에 있는가
2. **타입 조합** — `PREDICATE_TYPES` 표가 요구하는 subject/object 타입인가
3. **설명성 문단** — 기관 소개·주소 문단에서 만든 가짜 절차 관계
4. **금지 엔티티** — 일반명사, 국가명, 날짜 단독, 문장 조각
5. **이름 표기 흔들림** — `사업자등록증사본` ↔ `사업자등록증 사본`

방침은 **"잘못된 관계가 들어가는 것보다 일부가 빠지는 쪽"** 이다.
무엇이 왜 막히는지는 [kb-known-issues.md](kb-known-issues.md)에 있다.

### 운영 스크립트

| 스크립트 | 용도 |
|---|---|
| `kb_reset.py` | 지식베이스 비우기 (제약·인덱스는 유지). `CONFIRM=yes` 필요 |
| `kb_integrity.py` | 적재 후 무결성 7항목 검사 (문서·청크 수, id 중복, 토큰 위반, dangling FOUND_IN/relation, orphan chunk, 관계 없는 엔티티) |
| `kb_org_audit.py` | ORGANIZATION 노드가 그래프에 필요한지 감사 |
| `copy_graph.py` | 다른 Neo4j 의 그래프를 그대로 복사 (LLM 미호출) |
| `collect_urls.py` | 웹 문서를 PDF 코퍼스로 변환 |

컨테이너에서는 stdin 으로 넘긴다:

```bash
docker compose exec -T backend python - < scripts/kb_integrity.py
```

---

## 3. 질의 응답 (`rag/`)

```
질문
 │
 ├─ faq.py            FAQ 즉답. 복합질문 지시어에 걸리면 건너뛴다
 ├─ runtime.py        언어 감지, 질문 유형 분류, fast/deep 판정
 ├─ engine.py         ★ 검색 오케스트레이터
 │   ├─ retrieval/linker.py           질문 → Entity id
 │   ├─ retrieval/graph_retriever.py  DDE 멀티홉 탐색
 │   ├─ retrieval/vector_retriever.py 임베딩 검색
 │   └─ _merge_and_rerank()           합산 점수로 재랭크
 └─ llm/{openai,gemini,ollama,hf}_client.py   답변 생성
```

진입점은 둘이다. `api/service.py:answer_question()` 이 서비스 경로,
`query_runner.py:run_query_loop()` 이 터미널 경로(`yhs --query`).

### 점수 계산 — 숫자는 전부 YAML에 있다

```
final = 0.33 × base + 0.53 × keyword + 0.14 × recency
```

`base` 는 출처에 따라 다르다. 그래프 연결 청크는 0.75 고정, 소스 라우팅된 청크는
0.9, 벡터 청크는 cosine 유사도 그대로.

가중치는 Optuna TPE(n=150, gold bigram recall 기준)로 탐색한 값이다.
**코드에 숫자를 박지 말 것** — [engine.py:43](../backend/src/yhs/rag/engine.py#L43) 이
`retrieval.yaml` 을 읽는다. 값을 바꿨으면
`experiments/weight_sweep_optuna.py` 로 재검증한다.

### 그래프 탐색이 필터로 동작하게 하는 두 장치

홉이 깊어질수록 점수를 반감시킨다 (`dde_score_by_hop`: 1.0 / 0.5 / 0.25 / 0.125).

그리고 `RELATED_TO` 는 탐색에서 **제외한다.** 의미가 가장 옅은 포괄 술어인데
팬아웃이 제일 크다(엔티티당 3.2). 이걸 따라 걸으면 hop=2 만 돌아도 KB 의 69%가
후보로 쏟아져, 실제 선별은 키워드 점수가 다 하고 그래프는 역할이 없어진다.

### 라우팅 청크 최소 자리 보장

`base_scores.routed` 를 1.0 으로 올려도 최종 기여는 0.33 을 넘지 못한다.
그래서 라우팅된 청크가 일반 청크에 점수로 밀려 통째로 탈락하는 일이 있었다.
`rerank.routed_min_slots: 2` 가 자리를 강제로 확보한다. 0 으로 두면 끈다.

---

## 4. 어디를 고치면 무엇이 바뀌나

**검색 품질** → [retrieval.yaml](../backend/config/retrieval.yaml)

| 키 | 현재 | 의미 |
|---|---|---|
| `weights.*` | 0.33 / 0.53 / 0.14 | 재랭크 배합비 |
| `rerank.min_chunk_score` | 0.3 | 이 미만 청크 제외 |
| `rerank.final_top_k` | 6 | LLM 에 넘길 근거 수 |
| `question_fit_threshold` | 0.03 | 미만이면 `no_answer` |
| `gate.min_top_score` | 0.25 | fast → deep 전환 문턱 |
| `gate.min_evidence_chunks` | 2 | 최소 근거 청크 수 |
| `entity_link.cosine_threshold` | 0.72 | 엔티티 링킹 유사도 하한 |

**문서를 교체했을 때** → [routing.yaml](../backend/config/routing.yaml) 의 파일명만
`data/sources/` 실제 파일과 맞춘다. 코드는 건드릴 필요 없다. CI 가 실재 여부를 검사한다.

**새 관계 타입을 넣고 싶을 때** → [domain.yaml](../backend/config/domain.yaml)
`allowed_predicates` 에 추가하고, `validation.py` 의 `PREDICATE_TYPES` 에
타입 조합을 등록한다. 둘 중 하나만 하면 조용히 버려진다.

**FAQ·크롤러** → [faq.yaml](../backend/config/faq.yaml) /
[crawler.yaml](../backend/config/crawler.yaml). `allowed_sites` 는 화이트리스트라
여기 없는 도메인은 절대 방문하지 않는다.

**비밀키·접속 주소·실행 모드** → `.env`. 같은 항목이 YAML 과 겹치면 환경변수가 이긴다.

---

## 5. 함정

**id 는 이름에서 만든다.** LLM 이 준 id 를 믿으면 안 된다. 스키마 예시 `"예: D-4"` 를
"일련번호를 매기라"로 해석해 청크마다 D-1, D-2… 를 새로 발급한 적이 있다.
`D-2 = '안내 동영상'` 이 되어 별칭표의 `유학비자 → D-2` 가 엉뚱한 노드를 가리켰다.
[ingestor.py](../backend/src/yhs/ingest/pipeline/ingestor.py) 가 이름에서 정규 id 를
만들고, 이름이 같은 엔티티는 한 노드로 합친다.

**조용한 실패를 의심하라.** 인제스트가 끝까지 돌고 엔티티도 적재됐는데 관계만
0건이면 LLM 추출이 전부 실패한 것이다. extractor 가 LLM 실패를 잡아 규칙 기반으로
폴백하기 때문에 정상 종료한다. [stats.py](../backend/src/yhs/ingest/stats.py) 가
실패 건수·사유를 인제스트 끝에 반드시 출력하므로 그 요약을 먼저 본다.

**재인제스트는 upsert 다.** 완전히 새로 만들려면 `kb_reset.py` 를 먼저 돌린다.

**orphan chunk 45건은 정상이다.** 관계 없는 기관 노드를 빼기로 한 결과이고,
전부 기관 소개·주소 문서다. 임베딩이 있으므로 벡터·키워드 검색으로는 닿는다.

**`.venv` 는 저장소 안에 있다.** ruff·pytest 설정에서 제외돼 있지만 검색 도구를
쓸 때는 직접 걸러야 한다.

---

## 6. 현재 적재 상태

```
문서 35    청크 147    엔티티 869    의미관계 543
```

무결성: dangling endpoint 0, 중복 관계 0, Entity type 누락 0, 임베딩 누락 0,
orphan chunk 45.

```
CONDITION 203  DOCUMENT 144  PRODUCT 128  PERSON_GROUP 117
PROCEDURE 113  VISA 88       ORGANIZATION 76

APPLIES_TO 181  REQUIRES 132  HAS_CONDITION 102  RELATED_TO 42
SUBMITTED_TO 41 ISSUED_BY 11  PRECEDES 11        HAS_EXCEPTION 7
CAN_TRANSITION_TO 7  PRODUCES 3  ISSUED_TO 2  ENABLES 2  BLOCKS 1  FOLLOWED_BY 1
```

---

## 관련 문서

- [README](../README.md) — 설치, 실행, API 명세
- [architecture.md](architecture.md) — 모듈·함수 단위 상세
- [kb-known-issues.md](kb-known-issues.md) — 지식베이스에 남은 문제와 그 이유
- [graph_rag.md](graph_rag.md) — 구축 파이프라인 개요
- [adr/0001](adr/0001-hybrid-retrieval.md) — 하이브리드 검색을 택한 이유
