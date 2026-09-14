"""
yhs — 동아대학교 외국인 유학생 지원 AI 에이전트.

패키지 구성:
  core/    설정 단일 진입점 (환경변수 + YAML)
  schema/  도메인 타입 (노드·엣지·검색 결과)
  infra/   외부 시스템 어댑터 (Neo4j, 임베딩 모델)
  ingest/  PDF → 그래프 KB 구축 파이프라인
  rag/     질의 시점 검색·생성 (그래프 + 벡터 + 웹)
  api/     FastAPI 애플리케이션
"""

__version__ = "2.0.0"
