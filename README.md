 # YHS Graph RAG

 이 저장소는 그래프 형태로 저장된 근거를 참조하는 에이전트 코드만 남긴 구성입니다.

 ## 남은 구조

 - [main.py](main.py): 유지되는 공용 진입점
 - [agent/](agent): 질의, 인제스트, 검색, LLM 연동
 - [graph_rag/](graph_rag): 공통 설정, Neo4j 저장소, 임베딩, 파이프라인, 스키마
 - [data/](data): 신선도 검사 등에 쓰이는 보조 데이터
 - [docs/](docs): 설명 문서와 결과 기록
 - [pdf/](pdf): 입력 PDF 자료
 - [requirements.txt](requirements.txt): 의존성 목록

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
