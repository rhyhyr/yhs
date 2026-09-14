"""
yhs/core/config.py

설정 값의 평면(flat) 뷰.

실제 값은 두 곳에서 온다.
  - 환경변수 / .env  → yhs.core.settings.Settings
  - backend/config/*.yaml → yhs.core.settings.load_config()

이 모듈은 그 둘을 합쳐 기존 코드가 쓰던 대문자 상수 이름으로 노출한다.
새로 작성하는 코드는 가능하면 settings 를 직접 쓰는 쪽이 낫다 —
이 모듈의 값은 import 시점에 고정되므로 런타임에 환경변수를 바꿔도
반영되지 않는다.

    from yhs.core.settings import get_settings, load_config
    s = get_settings()
"""

from __future__ import annotations

from pathlib import Path

from yhs.core.settings import (
    BACKEND_DIR,
    PACKAGE_DIR,
    REPO_ROOT,
    _override,
    get_settings,
    load_config,
)

_s = get_settings()
_retrieval = load_config("retrieval")
_domain = load_config("domain")

# ─── 경로 ────────────────────────────────────────────────────────────────────
BASE_DIR = REPO_ROOT
DATA_DIR: Path = _s.data_dir
CONFIG_DIR: Path = _s.config_dir
PDF_DIR: Path = _s.sources_dir
REVIEW_QUEUE_PATH: Path = _s.review_queue
EMBED_CACHE_PATH: Path = _s.embed_cache

# ─── Neo4j ───────────────────────────────────────────────────────────────────
NEO4J_URI = _s.neo4j_uri
NEO4J_USER = _s.neo4j_user
NEO4J_PASSWORD = _s.neo4j_password
NEO4J_DATABASE = _s.neo4j_database
# Neo4j 5.11+ 네이티브 벡터 인덱스 사용 여부 (False 시 numpy fallback)
USE_NEO4J_VECTOR_INDEX = _s.use_neo4j_vector_index

# ─── 임베딩 모델 ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL = _s.embedding_model
EMBEDDING_DIM = _s.embedding_dim
EMBEDDING_BATCH_SIZE = _s.embedding_batch_size

# ─── LLM ─────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = _s.openai_api_key
OPENAI_MODEL = _s.openai_model
GEMINI_API_KEY = _s.gemini_api_key
GEMINI_MODEL = _s.gemini_model
OLLAMA_BASE_URL = _s.ollama_base_url
OLLAMA_MODEL = _s.ollama_model
OLLAMA_TIMEOUT = _s.ollama_timeout

# ─── 파이프라인 ───────────────────────────────────────────────────────────────
CHUNK_SIZE = _s.chunk_size          # 청크 목표 토큰 수
CHUNK_OVERLAP = _s.chunk_overlap    # 인접 청크 간 겹침 토큰 수
MAX_CHUNK_TOKENS = _s.max_chunk_tokens
MIN_CHUNK_TOKENS = _s.min_chunk_tokens
CONFIDENCE_THRESHOLD = _s.confidence_threshold
DOC_STALENESS_MONTHS = _s.doc_staleness_months
FRESHNESS_CHECK_INTERVAL_WEEKS = _s.freshness_check_interval_weeks

# ─── 검색(Retrieval) — backend/config/retrieval.yaml ─────────────────────────
_graph = _retrieval["graph"]
_link = _retrieval["entity_link"]

ENTITY_LINK_COSINE_THRESHOLD = _override(_link["cosine_threshold"], _s.entity_link_cosine_threshold)
ENTITY_LINK_TOP_K = _override(_link["top_k"], _s.entity_link_top_k)
DEFAULT_HOP_DEPTH = _override(_graph["default_hop_depth"], _s.default_hop_depth)
TOP_K_GRAPH_DEFAULT = _override(_graph["top_k_graph"], _s.top_k_graph_default)
TOP_K_VECTOR = _override(_graph["top_k_vector"], _s.top_k_vector)
MIN_CHUNKS_FROM_GRAPH = _override(_graph["min_chunks_from_graph"], _s.min_chunks_from_graph)

# DDE 스코어: 홉 거리별 가중치 (Mean Propagation)
DDE_SCORE_BY_HOP: dict[int, float] = {int(k): float(v) for k, v in _graph["dde_score_by_hop"].items()}

# 거리 무관 강제 포함 엣지 타입
ALWAYS_INCLUDE_EDGE_TYPES: list[str] = list(_graph["always_include_edge_types"])

# 탐색에서 제외할 엣지 타입 (포괄 술어가 팬아웃을 폭발시키는 것을 막는다)
TRAVERSAL_EXCLUDE_EDGE_TYPES: list[str] = list(
    _graph.get("traversal_exclude_edge_types", [])
)

# ─── 도메인 상수 — backend/config/domain.yaml ────────────────────────────────
KNOWN_INSTITUTIONS: list[str] = list(_domain["known_institutions"])
ALLOWED_PREDICATES: list[str] = list(_domain["allowed_predicates"])
ALIASES_MAP: dict[str, str] = dict(_domain["aliases"])

# ─── 메시지 템플릿 ────────────────────────────────────────────────────────────
DISCLAIMER_TEMPLATE = _domain["messages"]["disclaimer_template"]
NO_ANSWER_RESPONSE = _domain["messages"]["no_answer"]

__all__ = [
    "BACKEND_DIR", "PACKAGE_DIR", "BASE_DIR", "DATA_DIR", "CONFIG_DIR",
    "PDF_DIR", "REVIEW_QUEUE_PATH", "EMBED_CACHE_PATH",
    "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE", "USE_NEO4J_VECTOR_INDEX",
    "EMBEDDING_MODEL", "EMBEDDING_DIM", "EMBEDDING_BATCH_SIZE",
    "OPENAI_API_KEY", "OPENAI_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL",
    "OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT",
    "CHUNK_SIZE", "CHUNK_OVERLAP", "MAX_CHUNK_TOKENS", "MIN_CHUNK_TOKENS", "CONFIDENCE_THRESHOLD",
    "DOC_STALENESS_MONTHS", "FRESHNESS_CHECK_INTERVAL_WEEKS",
    "ENTITY_LINK_COSINE_THRESHOLD", "ENTITY_LINK_TOP_K", "DEFAULT_HOP_DEPTH",
    "TOP_K_GRAPH_DEFAULT", "TOP_K_VECTOR", "MIN_CHUNKS_FROM_GRAPH",
    "DDE_SCORE_BY_HOP", "ALWAYS_INCLUDE_EDGE_TYPES", "TRAVERSAL_EXCLUDE_EDGE_TYPES",
    "KNOWN_INSTITUTIONS", "ALLOWED_PREDICATES", "ALIASES_MAP",
    "DISCLAIMER_TEMPLATE", "NO_ANSWER_RESPONSE",
]
