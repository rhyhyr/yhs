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