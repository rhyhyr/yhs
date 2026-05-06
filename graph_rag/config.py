"""
graph_rag/config.py

역할: 전체 시스템에서 공유하는 상수·경로·모델명·임계값을 한 곳에서 관리한다.
      환경변수로 오버라이드 가능하도록 os.environ.get() 패턴을 사용한다.
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_env(path: str = ".env") -> None:
    """python-dotenv 없이 .env 파일을 읽어 환경변수를 채운다."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)


_load_env()

# ─── 경로 ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REVIEW_QUEUE_PATH = Path(os.environ.get("REVIEW_QUEUE_PATH", str(DATA_DIR / "review_queue.json")))
EMBED_CACHE_PATH = Path(os.environ.get("EMBED_CACHE_PATH", str(DATA_DIR / "embed_cache.pkl")))
PDF_DIR = Path(os.environ.get("PDF_DIR", str(BASE_DIR / "pdf")))

# ─── Neo4j ───────────────────────────────────────────────────────────────────
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", os.environ.get("NEO4J_USERNAME", "neo4j"))
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
# Neo4j 5.11+ 네이티브 벡터 인덱스 사용 여부 (False 시 numpy fallback)
USE_NEO4J_VECTOR_INDEX = os.environ.get("USE_NEO4J_VECTOR_INDEX", "true").lower() == "true"

# ─── 임베딩 모델 ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1024"))
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "32"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.0-flash")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "exaone3.5:7b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))

# ─── 파이프라인 ───────────────────────────────────────────────────────────────
MAX_CHUNK_TOKENS = int(os.environ.get("MAX_CHUNK_TOKENS", "512"))
MIN_CHUNK_TOKENS = int(os.environ.get("MIN_CHUNK_TOKENS", "50"))
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.7"))
DOC_STALENESS_MONTHS = int(os.environ.get("DOC_STALENESS_MONTHS", "6"))

# ─── 검색(Retrieval) ─────────────────────────────────────────────────────────
ENTITY_LINK_COSINE_THRESHOLD = float(os.environ.get("ENTITY_LINK_COSINE_THRESHOLD", "0.72"))
ENTITY_LINK_TOP_K = int(os.environ.get("ENTITY_LINK_TOP_K", "3"))
DEFAULT_HOP_DEPTH = int(os.environ.get("DEFAULT_HOP_DEPTH", "2"))
TOP_K_GRAPH_DEFAULT = int(os.environ.get("TOP_K_GRAPH_DEFAULT", "8"))
TOP_K_VECTOR = int(os.environ.get("TOP_K_VECTOR", "5"))
MIN_CHUNKS_FROM_GRAPH = int(os.environ.get("MIN_CHUNKS_FROM_GRAPH", "2"))

# DDE 스코어: 홉 거리별 가중치 (Mean Propagation)
DDE_SCORE_BY_HOP: dict[int, float] = {0: 1.0, 1: 0.5, 2: 0.25, 3: 0.125}

# 거리 무관 강제 포함 엣지 타입 (BLOCKS, ENABLES_SHORTCUT)
ALWAYS_INCLUDE_EDGE_TYPES: list[str] = ["BLOCKS", "ENABLES_SHORTCUT"]

# ─── 스케줄러 ─────────────────────────────────────────────────────────────────
FRESHNESS_CHECK_INTERVAL_WEEKS = int(os.environ.get("FRESHNESS_CHECK_INTERVAL_WEEKS", "1"))

# ─── 도메인 상수 ──────────────────────────────────────────────────────────────
KNOWN_INSTITUTIONS: list[str] = [
    "출입국관리사무소", "국민건강보험공단", "하이코리아",
    "외국인종합안내센터", "동아대학교", "국제교류처",
    "법무부", "고용노동부",
]

ALLOWED_PREDICATES: list[str] = [
    "CAN_TRANSITION_TO", "REQUIRES", "BLOCKS",
    "NEXT_STEP", "ISSUED_BY", "RELATED_TO", "ENABLES_SHORTCUT",
]

# aliases 사전: 비표준 표현 → 표준 ID
ALIASES_MAP: dict[str, str] = {
    "D2": "D-2",
    "D4": "D-4",
    "F5": "F-5",
    "영주권": "F-5",
    "어학원비자": "D-4",
    "일반연수비자": "D-4",
    "유학비자": "D-2",
    "어학연수비자": "D-4",
    "학생비자": "D-2",
}

# ─── 메시지 템플릿 ────────────────────────────────────────────────────────────
DISCLAIMER_TEMPLATE = (
    "\n\n⚠️  이 정보는 [{source_file}] ({doc_version}) 기준입니다. "
    "최신 정보는 하이코리아(hikorea.go.kr) 또는 외국인종합안내센터(1345)에서 확인하세요."
)
NO_ANSWER_RESPONSE = (
    "죄송합니다. 해당 정보를 찾을 수 없습니다. "
    "외국인종합안내센터(☎ 1345)에 문의하시거나 하이코리아(hikorea.go.kr)를 방문해 주세요."
)
