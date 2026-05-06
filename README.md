# Global Campus Visa Navigator RAG

> 외국인 유학생 비자·학사 안내 근거중심 도우미

## 문제 정의

외국인 유학생은 대학 안내, 체류자격(비자), 출입국 신고 의무를 서로 다른 문서에서 확인해야 한다. 문서마다 표현 방식이 달라 단순 검색으로는 맞는 조항을 빠르게 찾기 어렵고, 잘못된 이해는 행정 불이익으로 이어질 수 있다. 이 프로젝트는 답변보다 **"근거 문서와 조항을 정확히 찾아 제시"** 하는 것을 핵심으로 한다.

## 핵심 기능

**1. 비자·학사 하이브리드 질의응답**
벡터 검색(문맥 의미) + 그래프 검색(자격/전환/의무 관계)을 결합하고, 답변에 근거 문서명·조항·인용 스니펫을 포함한다.

**2. 정책 문서 중심 인덱싱 파이프라인**
PDF 로딩, 청킹, 임베딩, 조항 단위 메타데이터 추출을 자동화하며 개정일/시행일 기준으로 최신 버전을 우선 노출한다.

**3. 리스크 최소화 응답 정책**
근거 부족 시 단정 답변을 금지하고, 민원 채널(하이코리아/1345) 안내를 자동 첨부하며 회귀 질문셋으로 정확도와 근거 충실도를 자동 점검한다.

## 기술 스택

| 분류 | 기술 |
|---|---|
| Language | Python 3.11+ |
| LLM | Gemini / OpenAI / Ollama |
| Retrieval | SentenceTransformers, Hybrid (Vector + Graph) |
| Graph DB | Neo4j |
| Data Processing | pdfplumber, custom chunker/extractor |
| DevOps | Git, GitHub |

## 16주 마일스톤

| 기간 | 목표 |
|---|---|
| W1-2 | 질문 시나리오 60개 수집, 성공 지표 정의 |
| W3-4 | PDF 코퍼스 분류, 메타데이터 스키마 설계 |
| W5-6 | 인덱싱 파이프라인 구현 및 초기 코퍼스 적재 |
| W7-8 | 하이브리드 검색 MVP + 중간 데모 |
| W9-10 | Fast/Deep 라우팅 고도화 |
| W11-12 | 회귀 테스트 자동화, SLA 추적 |
| W13-14 | 운영 안정화, 발표 시연 시나리오 |
| W15 | 성능 튜닝, 문서화 |
| W16 | 최종 발표 및 데모 |
 ## 폴더 구조

- [main.py](main.py): 공용 진입점
- [agent/](agent): 질의, 인제스트, 검색, LLM 연동
- [graph_rag/](graph_rag): Neo4j 저장소, 임베딩, 파이프라인
- [docs/](docs): 설명 문서와 결과 기록
- [pdf/](pdf): 입력 PDF 자료

 ## 실행

 ```powershell
 python main.py --ingest
 python main.py --query
 python main.py --embed-update
 python main.py --freshness-check
 ```

 패키지 진입점도 사용할 수 있습니다.

 ```powershell
 python -m agent --ingest
 python -m agent --query
 python -m agent --embed-update
 python -m agent --freshness-check
 ```

 ## 환경변수

 ```env
 NEO4J_URI=bolt://localhost:7687
 NEO4J_USER=neo4j
 NEO4J_PASSWORD=YOUR_PASSWORD
 PDF_DIR=C:\path\to\pdf
 GEMINI_API_KEY=YOUR_GEMINI_API_KEY
 GEMINI_MODEL=gemini-3.0-flash
 GATE_MIN_TOP_SCORE=0.25
 GATE_MIN_EVIDENCE=2
 ENABLE_EXTERNAL_SEARCH=1
 ALLOWED_EXTERNAL_SUFFIXES=go.kr,ac.kr,gov,edu,gov.cn,edu.cn,ac.uk,gov.uk
 LATENCY_LOG_PATH=logs/latency_log.jsonl
 ```

 ## 설치

 ```powershell
 python -m pip install neo4j google-generativeai pdfplumber numpy scikit-learn sentence-transformers==3.0.1
 python -m pip install --upgrade torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
 ```

- [main.py](main.py): 유지되는 공용 진입점
- [agent/](agent): 질의, 인제스트, 검색, LLM 연동
- [graph_rag/](graph_rag): 공통 설정, Neo4j 저장소, 임베딩, 파이프라인, 스키마
- [README.md](README.md): 현재 남아 있는 구조 설명

## 실행

엔트리포인트는 `main.py`이며, 패키지 실행도 함께 지원합니다.

```powershell
python main.py --ingest
python main.py --query
python main.py --embed-update
python main.py --freshness-check

python -m agent --ingest
python -m agent --query
python -m agent --embed-update
python -m agent --freshness-check
```

## 환경변수

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_PASSWORD
PDF_DIR=C:\path\to\pdf
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.0-flash
GATE_MIN_TOP_SCORE=0.25
GATE_MIN_EVIDENCE=2
ENABLE_EXTERNAL_SEARCH=1
ALLOWED_EXTERNAL_SUFFIXES=go.kr,ac.kr,gov,edu,gov.cn,edu.cn,ac.uk,gov.uk
LATENCY_LOG_PATH=logs/latency_log.jsonl
```

## 의존성

```powershell
python -m pip install neo4j google-generativeai pdfplumber numpy scikit-learn sentence-transformers==3.0.1
python -m pip install --upgrade torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

### B. SentenceTransformer 초기화 실패(보안 정책)

- 원인: torch 2.6 미만
- 해결: torch를 `2.6.0+cpu` 이상으로 업그레이드

### C. huggingface symlink 경고

- 기능 문제는 아님(캐시 효율 경고)
- 필요 시 Windows 개발자 모드 활성화 또는 아래 환경변수 사용:

```powershell
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

## 9) 결과 검증 Cypher

```cypher
MATCH (ch:Chunk)-[:BELONGS_TO]->(c:Category)
WHERE c.level = 1
RETURN c.name AS subcategory, count(ch) AS chunks
ORDER BY chunks DESC;
```

```cypher
MATCH (ch:Chunk)
WHERE NOT (ch)-[:BELONGS_TO]->(:Category)
RETURN count(ch) AS orphan_chunks;
```

`orphan_chunks = 0`이면 연결 무결성은 정상입니다.

## 10) GitHub Actions 최적화

이 저장소에는 Matrix CI, Reusable Workflow, Composite Action, 선택적 배포 파이프라인이 포함되어 있습니다.

- 메인 워크플로: [.github/workflows/ci-and-selective-deploy.yml](.github/workflows/ci-and-selective-deploy.yml)
- 재사용 워크플로: [.github/workflows/python-matrix-reusable.yml](.github/workflows/python-matrix-reusable.yml)
- composite action: [.github/actions/pip-cache-benchmark/action.yml](.github/actions/pip-cache-benchmark/action.yml)

실행 시 각 매트릭스 조합마다 캐시 전후 설치 시간이 측정되며, GitHub Actions run 링크와 함께 Markdown 리포트가 아티팩트로 업로드됩니다.


![alt text](image-1.png)
