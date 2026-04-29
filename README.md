# Neo4j PDF Indexing (저장 전용)

이 프로젝트는 PDF 문서를 계층 카테고리 그래프로 변환하여 Neo4j에 저장합니다.
질의/답변은 포함하지 않고, DB 저장 파이프라인만 실행합니다.

![alt text](image.png)

## 1) 폴더 구조

- `hierarchical_rag.py`: 실행 엔트리포인트
- `student_agent.py`: 사용자 프로필/대화맥락 기반 QA 에이전트 (Fast/Deep 경로 적용)
- `hybrid_query_agent.py`: 하이브리드 검색 기반 QA 에이전트 (Fast/Deep 경로 적용)
- `agent_runtime.py`: 답변용 공통 구조 통합 파일 (fast/deep/policy/template/web/log)
- `regression_test.py`: 샘플 질문 회귀 테스트 및 SLA 점검
- `indexing/config.py`: .env 로딩, 설정값, 환경 검증
- `indexing/parser.py`: PDF 텍스트 추출/청킹
- `indexing/categorizer.py`: Gemini 기반 카테고리 생성 + 폴백
- `indexing/embedder.py`: SentenceTransformer 임베딩 + 폴백
- `indexing/store.py`: Neo4j 저장(MERGE)
- `indexing/indexer.py`: 단일 PDF 인덱싱 오케스트레이션
- `indexing/pipeline.py`: 폴더 단위 일괄 인덱싱

## 2) 필수 설치

PowerShell에서 실행:

```powershell
python -m pip install neo4j google-generativeai pdfplumber numpy scikit-learn sentence-transformers==3.0.1
python -m pip install --upgrade torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

## 3) .env 설정

프로젝트 루트에 `.env` 파일:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.0-flash

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_NEO4J_PASSWORD

PDF_DIR=C:\Users\<USER>\neo4j\pdf

# Indexing tuning
CHUNK_SIZE=380
CHUNK_OVERLAP=76
SIM_THRESHOLD=0.27
```

## 4) 실행 방법

```powershell
python hierarchical_rag.py
```

실행 동작:

1. `PDF_DIR`의 `*.pdf` 스캔
2. `doc_key` 기준으로 이미 저장된 파일은 스킵
3. 신규 파일만 Document/Category/Chunk 및 관계 저장

## 5) QA Fast/Deep 운영 기준

- 기본 경로: 1-hop Fast Path (RAG 1회 검색)
- Deep 진입 조건: 상위 점수 미달, 근거 수 부족, 비교/원인/예외형 질문
- SLA 목표: Fast 5초 이내, Deep 10초 이내
- 답변 정책: 사고 과정 비공개, 근거 요약만 노출
- 외부 검색: 근거 부족 시에만 사용, 정부/대학 공식 도메인 화이트리스트만 허용
- 지연 로그: `logs/latency_log.jsonl`

권장 환경변수:

```env
GATE_MIN_TOP_SCORE=0.25
GATE_MIN_EVIDENCE=2
ENABLE_EXTERNAL_SEARCH=1
ALLOWED_EXTERNAL_SUFFIXES=go.kr,ac.kr,gov,edu,gov.cn,edu.cn,ac.uk,gov.uk
LATENCY_LOG_PATH=logs/latency_log.jsonl
```

## 6) 회귀 테스트

```powershell
python regression_test.py --agent both
```

출력 항목:

1. `path` (fast/deep)
2. `elapsed_sec`
3. `best_score`
4. `sla_ok`

## 7) 저장 스키마 요약

- `(:Document {doc_key, file_path, indexed_at})`
- `(:Category {node_id, name, level, keywords_json, embedding_json, doc_key})`
- `(:Chunk {chunk_id, text, page, embedding_json, doc_key})`
- `(:Document)-[:HAS_CATEGORY]->(:Category {level:0})`
- `(:Category)-[:HAS_SUBCATEGORY]->(:Category {level:1})`
- `(:Chunk)-[:BELONGS_TO]->(:Category {level:1})`

## 8) 자주 발생하는 이슈

### A. torch DLL 오류(WinError 1114/126)

```powershell
python -m pip uninstall -y torch torchvision torchaudio
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