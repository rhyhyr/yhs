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

| | |
|---|---|
| **검색** | Neo4j 그래프(자격·전환·의무 관계) + BAAI/bge-m3 벡터(문맥 의미) 하이브리드 |
| **경로 분기** | fast path(단일 문서 즉답) / deep path(쿼리 확장 + 멀티 문서 + 웹 크롤링) |
| **코퍼스** | 하이코리아·출입국·NHIS·동아대 등 공식 문서 35종 |
| **LLM** | OpenAI / Gemini / Ollama(EXAONE) / HuggingFace — 설정으로 교체 |

---

## 처음 실행하기

필요한 건 **Docker Desktop** 하나뿐입니다. Python·Node 를 따로 설치하지 않아도 됩니다.

```bash
git clone https://github.com/rhyhyr/yhs.git
cd yhs
```

모든 명령은 `scripts/` 의 실행 스크립트를 통합니다. OS 에 맞는 쪽을 쓰세요.
어떤 명령을 실제로 실행하는지 매번 출력해 주므로, 익숙해지면 그대로 직접 쓰셔도 됩니다.

| | |
|---|---|
| Windows (PowerShell) | `.\scripts\dev.ps1 <명령>` |
| macOS / Linux / Git Bash | `./scripts/dev.sh <명령>` |

```powershell
.\scripts\dev.ps1 help     # 전체 명령 목록
.\scripts\dev.ps1 up       # 스택 기동 (.env 가 없으면 템플릿을 만들어 줍니다)
```

처음 `up` 을 실행하면 `.env` 가 없다고 알려 주며 `.env.example` 을 복사해 줍니다.
열어서 최소한 두 개를 채운 뒤 다시 `up` 하세요.

```ini
NEO4J_PASSWORD=원하는_비밀번호
OPENAI_API_KEY=sk-...        # RUNTIME_LLM=openai 로 쓸 때
```

기동 후 접속 주소:

| 주소 | 내용 |
|---|---|
| http://localhost:3000 | 프론트엔드 |
| http://localhost:8000/docs | API 문서 (Swagger — 여기서 바로 질의해 볼 수 있습니다) |
| http://localhost:7474 | Neo4j 브라우저 |

백엔드는 임베딩 모델(BAAI/bge-m3, 약 2GB)을 처음 한 번 내려받느라 **1~3분** 걸립니다.
`.\scripts\dev.ps1 logs` 로 진행 상황을 볼 수 있고, 준비되면 `/health` 가 `ok` 를 반환합니다.

### 지식베이스 채우기 (필수)

문서 검색은 Neo4j 에 적재된 지식베이스가 있어야 동작합니다. 비어 있으면
웹 크롤링으로만 답하고 근거 출처가 나오지 않습니다.

```powershell
.\scripts\dev.ps1 kb-status    # 현재 적재 상태 확인
.\scripts\dev.ps1 ingest       # data/sources 의 PDF 35종을 적재
```

`ingest` 는 PDF 마다 LLM 을 불러 엔티티·관계를 뽑으므로 시간과 API 비용이 듭니다.
**이미 다른 Neo4j 에 지식베이스를 만들어 두었다면** 재인제스트 대신 그대로 옮기세요 —
LLM 을 부르지 않아 비용이 0 입니다.

```powershell
.\scripts\dev.ps1 migrate-kb   # 기본 원본: 호스트의 Neo4j (host.docker.internal:7687)
.\scripts\dev.ps1 migrate-kb neo4j://다른주소:7687
```

### 전체 명령

```
도커로 전체 실행
  up             스택 기동 (CPU torch) — 처음이라면 이것부터
  up-gpu         스택 기동 (CUDA torch + GPU 할당, NVIDIA 필요)
  down           스택 정지·정리
  restart        스택 재기동
  build          이미지만 빌드
  logs [서비스]  로그 추적 (기본: backend)
  ps             컨테이너 상태

지식베이스
  ingest         data/sources 의 PDF 를 Neo4j 에 적재 (LLM 호출·비용 발생)
  migrate-kb     다른 Neo4j 의 그래프를 컨테이너로 복사 (LLM 미사용)
  kb-status      적재 상태 확인 (노드·청크 수)

도커 없이 로컬 개발
  install        백엔드·프론트 의존성 설치
  backend        백엔드 개발 서버 (http://localhost:8000)
  frontend       프론트 개발 서버 (http://localhost:5173)
  cli            터미널 질의 루프

품질
  test           백엔드 단위 테스트
  lint           파이썬 + 프론트 린트
  fmt            자동 수정 가능한 린트 문제 고치기
  clean          캐시·빌드 산출물 정리
```

### GPU 로 실행하기

기본 이미지는 CPU 전용 torch 를 씁니다 (어디서나 돌고 가볍습니다).
NVIDIA GPU 가 있다면 CUDA 빌드로 바꿔 임베딩과 로컬 LLM 추론을 가속할 수 있습니다.

```powershell
# 먼저 도커에서 GPU 가 보이는지 확인
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi

.\scripts\dev.ps1 up-gpu
```

실제로 GPU 를 쓰고 있는지는 백엔드 로그에서 확인합니다:

```
임베딩 모델 로드 완료: BAAI/bge-m3 (device=cuda:0)
```

`device=cpu` 로 나오면 CPU 이미지로 떠 있는 것입니다.

---

## 도커 없이 로컬 개발

코드를 고치며 개발할 때는 이쪽이 편합니다. Python 3.10+ 와 Node 20+ 가 필요합니다.
Neo4j 는 여전히 필요하므로 `up` 으로 띄워 두거나 별도 설치본을 쓰세요.

```powershell
.\scripts\dev.ps1 install     # 백엔드(editable) + 프론트 의존성
.\scripts\dev.ps1 backend     # http://localhost:8000  (코드 수정 시 자동 재시작)
.\scripts\dev.ps1 frontend    # http://localhost:5173
.\scripts\dev.ps1 cli         # 터미널에서 바로 질의
```

`vite.config.js` 가 `/api` 요청을 `localhost:8000` 으로 프록시하므로 프론트에
백엔드 주소를 넣을 필요가 없습니다. 백엔드 없이 화면만 보려면 `frontend/.env` 에
`VITE_USE_MOCK=true` 를 넣으면 mock 데이터로 동작합니다.

스크립트를 거치지 않고 직접 실행하려면:

```bash
cd backend && pip install -e ".[dev]" && playwright install chromium
uvicorn yhs.api.main:app --reload
yhs --ingest          # 지식베이스 구축
yhs --query           # 터미널 질의 루프
pytest -m "not integration"

cd frontend && npm ci && npm run dev
```

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
├── scripts/
│   ├── dev.ps1 / dev.sh ★ 모든 실행 명령의 진입점
│   ├── collect_urls.py  웹 문서 → PDF 코퍼스 수집
│   └── copy_graph.py    Neo4j 간 그래프 이관
└── docker-compose.yml
```

---

## 설정은 어디에 있나

값의 성격에 따라 두 곳으로 나뉜다. **겹치면 환경변수가 이긴다.**

| | 위치 | 담는 것 | git |
|---|---|---|---|
| 환경 | `.env` | 비밀키, 접속 주소, 실행 모드 | 제외 |
| 튜닝 | `backend/config/*.yaml` | 가중치, 임계값, 라우팅 표, FAQ 문안 | 추적 |

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

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/health` | 헬스체크 (`starting` / `ok`) |
| `POST` | `/api/chat` | 질의응답 — 근거 출처 포함 |
| `POST` | `/query` | 구버전 계약 (deprecated) |

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

| 목적 | `.env` 설정 |
|---|---|
| OpenAI | `RUNTIME_LLM=openai` + `OPENAI_API_KEY=...` |
| Gemini | `RUNTIME_LLM=gemini` + `GEMINI_API_KEY=...` |
| Ollama (로컬) | `RUNTIME_LLM=ollama` + `docker compose --profile ollama up -d` |
| HuggingFace (로컬) | `RUNTIME_LLM=hf` |

`LLM_PROVIDER` 는 지식베이스 구축(인제스트)용, `RUNTIME_LLM` 은 답변 생성용으로
따로 고를 수 있다.

---

## 실험 · 평가

평가 러너는 Neo4j 에 지식베이스가 적재돼 있어야 동작한다. 저장소 루트에서 실행한다
(러너가 `backend/src` 를 경로에 넣어 주므로 `pip install -e backend` 는 없어도 된다).

```bash
python experiments/run_eval100_openai.py       # N=100 평가 러너
python experiments/weight_sweep_optuna.py      # 검색 가중치 Optuna 스윕
python experiments/zh_eval.py                  # 중국어 번역 on/off 비교
```

검색 파라미터는 환경변수로 임시 오버라이드할 수 있다 (YAML 을 건드리지 않고 스윕):

```bash
TOP_K_VECTOR=8 GATE_MIN_TOP_SCORE=0.3 python experiments/run_eval100_openai.py
```

데이터셋은 `experiments/eval_sets/`, 결과는 `experiments/results/` 에 쌓인다
(결과는 용량이 커서 git 에서 제외된다). 평가 프로토콜은
[docs/experiments/](docs/experiments/) 참고.

---

## 배포

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

compose 오버라이드 파일은 용도별로 나뉜다.

| 파일 | 용도 |
|---|---|
| `docker-compose.yml` | 기본 (개발용, 포트 전부 공개) |
| `deploy/docker-compose.gpu.yml` | CUDA torch + GPU 할당 |
| `deploy/docker-compose.prod.yml` | 운영 — 포트 비공개, 재시작 정책, 로그 제한 |

운영 오버라이드는 백엔드·Neo4j 포트를 외부에 열지 않고 nginx(프론트 컨테이너)만
80 포트로 노출한다. nginx 가 `/api` 를 백엔드로 프록시하므로 프론트와 API 가 같은
오리진이 되고, CORS 설정이 필요 없다.

`main` 에 머지되면 CD 워크플로우가 이미지를 GHCR 에 올린다.

---

## 라이선스

[MIT](LICENSE)
