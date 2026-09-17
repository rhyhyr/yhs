# yhs backend

동아대학교 외국인 유학생 지원 AI 에이전트의 백엔드.
Neo4j 그래프 + BAAI/bge-m3 벡터 하이브리드 RAG와 FastAPI 서버를 제공한다.

## 구조

| 경로 | 역할 |
|------|------|
| `src/yhs/core/` | 설정 단일 진입점 (환경변수 + `config/*.yaml`) |
| `src/yhs/schema/` | 도메인 타입 (노드·엣지·검색 결과) |
| `src/yhs/infra/` | 외부 시스템 어댑터 (Neo4j, 임베딩 모델, 신선도) |
| `src/yhs/ingest/` | PDF → 그래프 KB 구축 파이프라인 |
| `src/yhs/rag/` | 질의 시점 검색·생성 (그래프 + 벡터 + 웹 크롤링) |
| `src/yhs/api/` | FastAPI 애플리케이션 |
| `config/` | 코드 밖으로 뺀 튜닝 파라미터 YAML |
| `tests/` | 단위·통합 테스트 |

## 개발 환경

```bash
pip install -e ".[dev]"
playwright install chromium   # 크롤러용

pytest                        # 단위 테스트
pytest -m integration         # Ollama 필요
uvicorn yhs.api.main:app --reload
yhs --ingest --pdf-dir ../data/sources   # KB 구축
```
