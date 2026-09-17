# 지식베이스 구축

PDF → 엔티티·관계 → Neo4j. 유학생 행정 도메인 전용 지식 그래프를 만드는 쪽 이야기다.
질의 응답은 [architecture.md](architecture.md#rag--질의-응답) 참고.

---

## 왜 그래프인가

이 프로젝트의 질문은 대부분 **"무엇이 먼저인가 / 무엇이 있어야 하는가 / 무엇이 막는가"**
형태다. 벡터 검색은 비슷한 문단을 찾아 줄 뿐 이 축을 못 따라간다.

그래서 관계를 명시적으로 저장한다 — 비자 간 전환 조건(`CAN_TRANSITION_TO`),
필요 서류(`REQUIRES`), 막는 조건(`BLOCKS`), 절차 순서(`PRECEDES`).
허용 술어 전체 목록은 [domain.yaml](../backend/config/domain.yaml) 에 있고,
여기 없는 술어는 인제스트 단계에서 버려진다.

---

## 3단계 파이프라인

```
scripts/kb_extract.py   LLM 추출 → data/extract/raw.jsonl        API 비용 발생
scripts/kb_analyze.py   검증 재적용 + 전수 분석 → validated.jsonl  API 호출 없음
scripts/kb_load.py      검증 통과분만 Neo4j 적재                  API 호출 없음
```

한 덩어리였을 때는 검증 규칙을 한 줄 고칠 때마다 147청크를 전부 다시 호출해야 했고,
무엇이 그래프에 들어갈지 미리 볼 수 없었다. 12청크 샘플로 통과 판정을 내렸다가
147청크 전수에서 문단유형 오분류 103건이 드러난 일이 실제로 있었다.

추출 캐시 키는 `(chunk_id, model, prompt_version, schema_hash)`.
프롬프트를 고쳐 `PROMPT_VERSION` 을 올리면 영향받은 청크만 다시 부른다.

### 실행

```bash
docker compose exec -T -e CONFIRM=yes backend python - < scripts/kb_reset.py
docker compose exec -T -e LLM_PROVIDER=openai backend python - < scripts/kb_extract.py
docker compose exec -T backend python - < scripts/kb_analyze.py    # 숫자 확인
docker compose exec -T backend python - < scripts/kb_load.py       # 납득되면 적재
docker compose exec -T backend python - < scripts/kb_integrity.py  # 검사
```

검증 규칙만 고쳤다면 `kb_analyze.py` → `kb_load.py` 두 개만 다시 돌리면 된다.
`data/extract/raw.jsonl` 이 저장소에 있으므로 API 비용은 들지 않는다.

특정 청크만 다시 뽑을 때는 `ONLY` 로 지정한다:

```bash
docker compose exec -T -e LLM_PROVIDER=openai -e ONLY=<chunk_id,...> \
    backend python - < scripts/kb_extract.py
```

> 추출부터 적재까지 한 번에 도는 `yhs --ingest` 도 남아 있다. 옛 경로다.

---

## 청크 하나가 처리되는 순서

```
loader.py     PDF → 페이지 텍스트 (pdfplumber)
cleaner.py    머리말·꼬리말 등 잡음 제거
chunker.py    페이지 경계를 넘어 이어 붙여 청크 생성 (상한 512토큰)
extractor.py  규칙 기반 + LLM 추출 병합
validation.py 그래프에 넣기 전 검사
ingestor.py   이름에서 정규 id 생성 후 Neo4j 적재
embedder.py   청크 임베딩 생성 (벡터 검색용)
```

---

## 모델

| 용도 | 모델 | 비용 |
|---|---|---|
| 엔티티·관계 추출 | `.env` 의 `OPENAI_MODEL` (최종 적재는 gpt-5 계열 mini) | 유료 |
| 임베딩 | `BAAI/bge-m3` (1024차원) | 무료 |

`LLM_PROVIDER` 로 공급자를 고른다 — `openai` / `gemini` / `ollama` / `exaone`(로컬 HF).

**로컬 모델과 OpenAI 는 채택률이 크게 다르다.** 로컬 Qwen 은 구조화 출력을 강제할
수단이 없어서, 프롬프트에 "relations 의 subject/object 는 entities 의 name 과 같아야
한다"고 써도 지키지 않으면 그대로 통과하고 검증에서 대량 폐기된다.

| 12청크 기준 | Qwen | gpt-5 계열 mini |
|---|---|---|
| 관계 채택률 | 8/130 = 6% | 100/119 = 84% |
| endpoint 누락 | 81 | 9 |
| 타입 불일치 | 41 | 10 |

OpenAI 는 `strict: true` json_schema 로 타입·술어·문단유형을 **디코딩 단계에서**
enum 으로 고정한다. 개발·로컬 테스트는 Qwen 을 그대로 쓰고, 최종 적재만
`-e LLM_PROVIDER=openai` 로 덮어썼다.

---

## 그래프에 들어가지 않는 것

방침은 **잘못된 관계가 들어가는 것보다 일부가 빠지는 쪽**이다.
[validation.py](../backend/src/yhs/ingest/validation.py) 가 다섯 가지를 막는다 —
endpoint 누락, 타입 조합 불일치, 설명성 문단의 가짜 절차 관계, 금지 엔티티,
이름 표기 흔들림.

관계가 하나도 없는 기관 노드도 빼기로 했다. 검색에 필요한 것은 "이름이 본문에 있다"
이지 "그래프에 노드가 있다"가 아니고, 이름은 청크 임베딩·키워드 검색으로 닿는다.

무엇이 왜 막히는지는 [kb-known-issues.md](kb-known-issues.md)에 항목별로 적혀 있다.

---

## 현재 적재 상태

```
문서 35    청크 147    엔티티 869    의미관계 543
```

무결성 검사(`kb_integrity.py`, 7항목): dangling endpoint 0, 중복 관계 0,
Entity type 누락 0, 임베딩 누락 0, orphan chunk 45.

orphan chunk 45건은 기관 노드 정리의 직접적 결과다. 전부 기관 소개·주소 문서이고,
임베딩이 있으므로 벡터·키워드 검색으로는 정상적으로 닿는다. 그래프 탐색 경로만 없다.
