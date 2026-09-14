"""
yhs/core/settings.py

설정 단일 진입점.

두 종류의 설정을 명확히 분리한다.

  환경(environment)  — `.env` / 환경변수
      비밀키, 접속 주소, 실행 모드처럼 배포 환경마다 달라지는 값.
      git 에 올리지 않는다.

  튜닝(tuning)       — `backend/config/*.yaml`
      가중치, 임계값, 라우팅 표, FAQ 문안처럼 "무엇이 옳은가"를 담은 값.
      git 으로 추적해 변경 이력과 diff 를 남긴다.

둘이 겹칠 때는 환경변수가 이긴다. 실험 스크립트가 환경변수만 바꿔
스윕을 돌릴 수 있어야 하기 때문이다.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 소스 트리에서 실행할 때 이 파일의 위치는
#   <repo>/backend/src/yhs/core/settings.py
#   parents[0]=core [1]=yhs [2]=src [3]=backend [4]=<repo>
# 휠로 설치된 경우(도커 이미지)에는 site-packages 아래이므로 위 가정이 깨진다.
# backend/pyproject.toml 이 실제로 있는지로 두 경우를 구분한다.
_HERE = Path(__file__).resolve()
PACKAGE_DIR = _HERE.parents[1]                       # .../yhs

_maybe_backend = _HERE.parents[3] if len(_HERE.parents) > 3 else PACKAGE_DIR
_IS_SOURCE_TREE = (_maybe_backend / "pyproject.toml").is_file()

BACKEND_DIR = _maybe_backend if _IS_SOURCE_TREE else PACKAGE_DIR
REPO_ROOT = _HERE.parents[4] if _IS_SOURCE_TREE else Path.cwd()

# 설정 YAML: 소스 트리면 backend/config, 설치본이면 패키지에 동봉된 yhs/_config.
_SOURCE_CONFIG = BACKEND_DIR / "config"
_BUNDLED_CONFIG = PACKAGE_DIR / "_config"
DEFAULT_CONFIG_DIR = _SOURCE_CONFIG if _SOURCE_CONFIG.is_dir() else _BUNDLED_CONFIG


class Settings(BaseSettings):
    """환경변수 + .env 로 주입되는 설정."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", Path(".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 경로 ────────────────────────────────────────────────────────────
    data_dir: Path = REPO_ROOT / "data"
    config_dir: Path = DEFAULT_CONFIG_DIR
    pdf_dir: Path | None = None          # 미설정 시 data_dir/sources
    review_queue_path: Path | None = None
    embed_cache_path: Path | None = None

    # ── Neo4j ───────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_USER", "NEO4J_USERNAME"),
    )
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    use_neo4j_vector_index: bool = True

    # ── 임베딩 ──────────────────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    embedding_batch_size: int = 32

    # ── LLM 공급자 선택 ─────────────────────────────────────────────────
    llm_provider: str = "ollama"    # KB 구축(인제스트)용
    runtime_llm: str = "ollama"     # 답변 생성용

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_runtime_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "exaone3.5:7.8b"
    ollama_timeout: int = 180

    hf_runtime_model: str = "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"

    # ── 파이프라인 ──────────────────────────────────────────────────────
    max_chunk_tokens: int = 512
    min_chunk_tokens: int = 50
    confidence_threshold: float = 0.7
    doc_staleness_months: int = 6
    freshness_check_interval_weeks: int = 1

    # ── 기능 토글 ───────────────────────────────────────────────────────
    enable_zh_translation: bool = True

    # ── API ─────────────────────────────────────────────────────────────
    # 운영에서는 nginx 가 프론트와 /api 를 같은 오리진으로 묶으므로 CORS 가
    # 필요 없다. 여기 값은 vite dev 서버에서 직접 호출할 때만 쓰인다.
    # 쉼표로 구분해 여러 개를 줄 수 있다. "*" 는 모든 오리진 허용 (개발 전용).
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins_raw"),
    )

    # ── YAML 튜닝값을 덮어쓰는 환경변수 (실험 스윕용) ───────────────────
    # None 이면 YAML 값을 그대로 쓴다.
    top_k_vector: int | None = None
    top_k_graph_default: int | None = None
    default_hop_depth: int | None = None
    min_chunks_from_graph: int | None = None
    entity_link_cosine_threshold: float | None = None
    entity_link_top_k: int | None = None
    gate_min_top_score: float | None = None
    gate_min_evidence: int | None = None
    vec_weight: float | None = None
    kw_weight: float | None = None
    crawl_max_depth: int | None = None
    crawl_max_pages: int | None = None
    crawl_fetch_timeout: int | None = None
    crawl_sleep_sec: float | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    # ── 파생 경로 ───────────────────────────────────────────────────────
    @property
    def sources_dir(self) -> Path:
        """인제스트 대상 PDF 디렉토리."""
        return self._abs(self.pdf_dir) if self.pdf_dir else self.data_dir / "sources"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def review_queue(self) -> Path:
        return self._abs(self.review_queue_path) if self.review_queue_path else self.cache_dir / "review_queue.json"

    @property
    def embed_cache(self) -> Path:
        return self._abs(self.embed_cache_path) if self.embed_cache_path else self.cache_dir / "embed_cache.pkl"

    @staticmethod
    def _abs(p: Path) -> Path:
        """상대 경로는 저장소 루트 기준으로 해석한다 (cwd 에 흔들리지 않도록)."""
        return p if p.is_absolute() else (REPO_ROOT / p)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@functools.cache
def load_config(name: str) -> dict[str, Any]:
    """backend/config/<name>.yaml 을 읽어 dict 로 돌려준다 (캐시됨)."""
    path = get_settings().config_dir / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def reload_config() -> None:
    """설정 캐시를 비운다 (테스트·실험에서 환경변수를 바꿔 가며 쓸 때)."""
    get_settings.cache_clear()
    load_config.cache_clear()


def _override(yaml_value: Any, env_value: Any) -> Any:
    """환경변수가 설정돼 있으면 그 값이 이긴다."""
    return yaml_value if env_value is None else env_value
