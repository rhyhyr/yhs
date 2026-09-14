# YHS — 동아대학교 외국인 유학생 AI 에이전트

> 유학생 비자·학사·생활 행정 질문에 **근거 문서를 함께 제시**하는 Graph RAG 챗봇

[![CI](https://github.com/rhyhyr/yhs/actions/workflows/ci.yml/badge.svg)](https://github.com/rhyhyr/yhs/actions/workflows/ci.yml)

---

## 무엇을 하는 프로젝트인가

외국인 유학생은 대학 안내, 체류자격(비자), 출입국 신고 의무를 서로 다른 기관의
문서에서 각각 확인해야 한다. 문서마다 표현이 달라 단순 검색으로는 맞는 조항을
찾기 어렵고, 잘못된 이해가 곧바로 행정 불이익으로 이어진다.

이 프로젝트는 답변 자체보다 **"근거 문서와 조항을 정확히 찾아 제시하는 것"** 을
목표로 한다. 근거가 부족하면 단정하지 않고 1345·하이코리아 안내로 넘긴다.

|                     |                                                                              |
| ------------------- | ---------------------------------------------------------------------------- |
| **검색**      | Neo4j 그래프(자격·전환·의무 관계) + BAAI/bge-m3 벡터(문맥 의미) 하이브리드 |
| **경로 분기** | fast path(단일 문서 즉답) / deep path(쿼리 확장 + 멀티 문서 + 웹 크롤링)     |
| **코퍼스**    | 하이코리아·출입국·NHIS·동아대 등 공식 문서 35종                           |
| **LLM**       | OpenAI / Gemini / Ollama(EXAONE) / HuggingFace — 설정으로 교체              |

---

## 빠른 시작 (Docker)

가장 빠른 길이다. Neo4j·백엔드·프론트가 한 번에 뜬다.

```bash
git clone https://github.com/rhyhyr/yhs.git
cd yhs

cp .env.example .env
# .env 를 열어 NEO4J_PASSWORD 와 사용할 LLM 의 API 키를 채운다

docker compose up -d --build
```

| 주소                       | 내용               |
| -------------------------- | ------------------ |
| http://localhost:3000      | 프론트엔드 (React) |
| http://localhost:8000/docs | API 문서 (Swagger) |
| http://localhost:7474      | Neo4j 브라우저     |

처음 한 번은 지식베이스를 만들어야 한다 (`data/sources/` 의 PDF → Neo4j):

```bash
docker compose exec backend yhs --ingest
```

이미 다른 Neo4j(예: 로컬 Neo4j Desktop)에 만들어 둔 지식베이스가 있다면,
재인제스트 대신 그대로 옮길 수 있다 — LLM 을 부르지 않으므로 API 비용이 들지 않는다:

```bash
docker compose exec -T   -e SRC_URI=neo4j://host.docker.internal:7687 -e SRC_PASSWORD=...   -e DST_URI=neo4j://neo4j:7687               -e DST_PASSWORD=...   backend python - < scripts/copy_graph.py
```

### GPU 로 실행하기

기본 이미지는 CPU 전용 torch 를 쓴다 (어디서나 돌고 3~4GB 가볍다).
NVIDIA GPU 가 있다면 CUDA 빌드로 바꿔 임베딩과 로컬 LLM 추론을 가속할 수 있다:

```bash
make up-gpu
# = docker compose -f docker-compose.yml -f deploy/docker-compose.gpu.yml up -d --build
```

먼저 도커에서 GPU 가 보이는지 확인한다:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

GPU 를 실제로 쓰고 있는지는 백엔드 로그에서 확인한다:

```
임베딩 모델 로드 완료: BAAI/bge-m3 (device=cuda:0)
```

로컬 LLM(Ollama)을 쓰려면 프로파일을 켜고 모델을 받는다:

```bash
docker compose --profile ollama up -d
docker compose exec ollama ollama pull exaone3.5:7.8b   # 약 5GB
```

---

## 로컬 개발 (도커 없이)

**백엔드**

```bash
cd backend
pip install -e ".[dev]"
playwright install chromium        # 크롤러가 JS 렌더링 페이지를 읽을 때 사용

pytest                             # 단위 테스트
uvicorn yhs.api.main:app --reload  # http://localhost:8000
yhs --ingest                       # 지식베이스 구축
yhs --query                        # 터미널 질의 루프
```

**프론트엔드**

```bash
cd frontend
npm ci
npm run dev                        # http://localhost:5173
```

`vite.config.js` 가 `/api` 요청을 `localhost:8000` 으로 프록시하므로
프론트에 백엔드 주소를 넣을 필요가 없다. 백엔드 없이 화면만 보려면
`frontend/.env` 에 `VITE_USE_MOCK=true` 를 넣으면 된다.

---

## 저장소 구조

```
yhs/
├── backend/
│   ├── src/yhs/
│   │   ├── core/        설정 단일 진입점 (환경변수 + YAML)
│   │   ├── schema/      도메인 타입 (노드·엣지·검색 결과)
│   │   ├── infra/       외부 시스템 어댑터 (Neo4j, 임베딩 모델)
│   │   ├── ingest/      PDF → 그래프 KB 구축 파이프라인
│   │   ├── rag/         질의 시점 검색·생성 (그래프 + 벡터 + 웹)
│   │   └── api/         FastAPI (routes / schemas / service / deps)
│   ├── config/          ★ 코드 밖으로 뺀 튜닝 파라미터 YAML
│   └── tests/
├── frontend/            React + Vite, nginx 로 서빙 (/api 리버스 프록시)
├── data/sources/        인제스트 대상 공식 문서 35종
├── experiments/         평가 러너와 데이터셋 (results/ 는 git 제외)
├── deploy/              운영 compose 오버라이드
├── docs/                설계 문서, ADR, 실험 프로토콜
├── scripts/             코퍼스 수집 도구
└── docker-compose.yml
```

---

## 설정은 어디에 있나

값의 성격에 따라 두 곳으로 나뉜다. **겹치면 환경변수가 이긴다.**

|      | 위치                       | 담는 것                             | git  |
| ---- | -------------------------- | ----------------------------------- | ---- |
| 환경 | `.env`                   | 비밀키, 접속 주소, 실행 모드        | 제외 |
| 튜닝 |  `backend/config/*.yaml` | 가중치, 임계값, 라우팅 표, FAQ 문안 | 추적 |

```
backend/config/
├── retrieval.yaml   재랭크 가중치·top_k·게이트 문턱값
├── routing.yaml     키워드 → 소스 파일 강제 라우팅 41개
├── crawler.yaml     허용 사이트 화이트리스트, 크롤 예산
├── faq.yaml         FAQ 20개, 복합질문 지시어 54개
└── domain.yaml      기관명, 관계 술어, 비자 별칭, 메시지 문안
```

검색 품질을 손보고 싶으면 코드가 아니라 `retrieval.yaml` 을 고친다.
문서를 교체했다면 `routing.yaml` 의 파일명만 맞춰 주면 된다
(CI 가 실재 여부를 검사한다).

환경변수로 일시적으로 덮어쓰는 건 실험 스윕용이다:

```bash
TOP_K_VECTOR=8 GATE_MIN_TOP_SCORE=0.3 python experiments/run_eval100_openai.py
```

---

## API

| 메서드   | 경로          | 설명                             |
| -------- | ------------- | -------------------------------- |
| `GET`  | `/health`   | 헬스체크 (`starting` / `ok`) |
| `POST` | `/api/chat` | 질의응답 — 근거 출처 포함       |
| `POST` | `/query`    | 구버전 계약 (deprecated)         |

```http
POST /api/chat
{ "channelId": "visa", "message": "비자 연장 언제부터 신청하나요?", "history": [] }

200 OK
{
  "answer": "D-2 비자 체류기간 연장은 만료일 4개월 전부터...",
  "sources": [
    { "id": "chunk-...", "label": "하이코리아 체류기간연장허가",
      "detail": "p.2 · 2025.06", "url": "", "score": 0.87 }
  ],
  "tags": [],
  "path": "fast"
}
```

---

## LLM 공급자 전환

| 목적               | `.env` 설정                                                      |
| ------------------ | ------------------------------------------------------------------ |
| OpenAI             | `RUNTIME_LLM=openai` + `OPENAI_API_KEY=...`                    |
| Gemini             | `RUNTIME_LLM=gemini` + `GEMINI_API_KEY=...`                    |
| Ollama (로컬)      | `RUNTIME_LLM=ollama` + `docker compose --profile ollama up -d` |
| HuggingFace (로컬) | `RUNTIME_LLM=hf`                                                 |

`LLM_PROVIDER` 는 지식베이스 구축(인제스트)용, `RUNTIME_LLM` 은 답변 생성용으로
따로 고를 수 있다.

---

## 실험 · 평가

```bash
python experiments/run_eval100_openai.py       # N=100 평가 러너
python experiments/weight_sweep_optuna.py      # 검색 가중치 Optuna 스윕
```

데이터셋은 `experiments/eval_sets/`, 결과는 `experiments/results/` 에 쌓인다
(결과는 용량이 커서 git 에서 제외된다). 평가 프로토콜은
[docs/experiments/](docs/experiments/) 참고.

---

## 배포

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

운영 오버라이드는 백엔드·Neo4j 포트를 외부에 열지 않고 nginx(프론트 컨테이너)만
80 포트로 노출한다. nginx 가 `/api` 를 백엔드로 프록시하므로 프론트와 API 가 같은
오리진이 되고, CORS 설정이 필요 없다.

`main` 에 머지되면 CD 워크플로우가 이미지를 GHCR 에 올린다.

---

## 라이선스

[MIT](LICENSE)
