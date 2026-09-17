"""
yhs/api/deps.py

애플리케이션 수명 동안 유지되는 무거운 리소스를 한 곳에서 관리한다.

Embedder(임베딩 모델)와 GraphStore(Neo4j 드라이버)는 생성 비용이 커서
요청마다 만들 수 없다. lifespan 에서 한 번 만들고 여기에 담아 둔다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from yhs.core.settings import get_settings
from yhs.infra.embedder import Embedder
from yhs.infra.graph_store import GraphStore
from yhs.rag.crawler.web_search_client import WebSearchClient, allowed_sites
from yhs.rag.engine import RetrievalEngine
from yhs.rag.faq import FastPathHandler
from yhs.rag.runtime import GateThresholds

logger = logging.getLogger(__name__)


def build_llm() -> Any:
    """RUNTIME_LLM 설정에 따라 답변 생성용 LLM 클라이언트를 만든다."""
    provider = get_settings().runtime_llm.lower()

    if provider == "gemini":
        from yhs.rag.llm.gemini_client import GeminiRuntimeClient

        client = GeminiRuntimeClient()
        if client.is_available():
            return client
        logger.warning("Gemini API 키가 없습니다 — Ollama 로 폴백합니다.")

    elif provider == "openai":
        from yhs.rag.llm.openai_client import OpenAIRuntimeClient

        client = OpenAIRuntimeClient()
        if client.is_available():
            return client
        logger.warning("OpenAI API 키가 없습니다 — Ollama 로 폴백합니다.")

    elif provider == "hf":
        from yhs.rag.llm.hf_client import HFRuntimeClient

        return HFRuntimeClient()

    from yhs.rag.llm.ollama_client import OllamaRuntimeClient

    client = OllamaRuntimeClient()
    if not client.is_available():
        logger.warning("Ollama 서버에 연결할 수 없습니다. 'ollama serve' 실행 여부를 확인하세요.")
    return client


def _build_openai_client() -> Any | None:
    """크롤러가 쓰는 OpenAI 클라이언트. 키가 없으면 None."""
    api_key = get_settings().openai_api_key.strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover - 선택적 의존성
        logger.warning("OpenAI 클라이언트 생성 실패: %s", exc)
        return None


@dataclass
class AppState:
    """lifespan 동안 살아 있는 싱글턴 묶음."""

    store: GraphStore
    engine: RetrievalEngine
    web_client: WebSearchClient
    llm: Any
    faq: FastPathHandler
    thresholds: GateThresholds
    http: requests.Session

    @classmethod
    def create(cls) -> AppState:
        http = requests.Session()
        embedder = Embedder()
        llm = build_llm()

        store = GraphStore()
        store.__enter__()

        engine = RetrievalEngine(store, embedder, ollama_client=llm)

        # 크롤러의 링크 선택/요약에는 Gemini 또는 OpenAI 를 쓴다.
        # (CLI 경로인 query_runner 와 동일하게 맞춘다 — 예전에는 API 쪽만
        #  openai_client=None 이라 크롤링 품질이 달랐다.)
        web_llm = llm if get_settings().runtime_llm.lower() == "gemini" else None
        openai_client = _build_openai_client()
        web_client = WebSearchClient(
            http, embedder, web_llm, store._driver, allowed_sites, openai_client=openai_client
        )
        return cls(
            store=store,
            engine=engine,
            web_client=web_client,
            llm=llm,
            faq=FastPathHandler(),
            thresholds=GateThresholds.from_config(),
            http=http,
        )

    def close(self) -> None:
        self.store.__exit__(None, None, None)
        self.http.close()
