"""
agent/retrieval/linker.py

역할: 사용자 질문에서 그래프의 Entity 노드를 찾는 Topic Entity 링킹.
      3단계(0~2) 순서로 시도하며, 성공 시 중단한다.
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np

from graph_rag.config import ALIASES_MAP, ENTITY_LINK_COSINE_THRESHOLD, ENTITY_LINK_TOP_K
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

logger = logging.getLogger(__name__)


class EntityLinker:
    """3단계 Topic Entity 링킹."""

    def __init__(self, store: GraphStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._entity_cache: list[dict] | None = None
        self._summary_embeddings: np.ndarray | None = None
        self._summary_ids: list[str] = []

    def _load_entity_cache(self) -> None:
        if self._entity_cache is not None:
            return
        self._entity_cache = self._store.get_all_entities_summary()
        summaries = [e.get("summary", e.get("name", "")) for e in self._entity_cache]
        self._summary_ids = [e["id"] for e in self._entity_cache]
        if summaries:
            self._summary_embeddings = self._embedder.encode(summaries)
        else:
            self._summary_embeddings = np.zeros((0, 1024), dtype=np.float32)

    def invalidate_cache(self) -> None:
        self._entity_cache = None
        self._summary_embeddings = None
        self._summary_ids = []

    def _step0_llm_normalize(self, question: str) -> str:
        try:
            from agent.ollama_client import OllamaRuntimeClient
            client = OllamaRuntimeClient()
            normalized = client.normalize_question(question)
            return normalized if normalized else question
        except Exception as exc:
            logger.warning("LLM 전처리 실패, 원본 질문 사용: %s", exc)
            return question

    def _step1_aliases_match(self, keyword: str) -> List[str]:
        keyword_lower = keyword.lower().strip()
        matched: List[str] = []

        for alias, standard_id in ALIASES_MAP.items():
            if alias.lower() in keyword_lower or keyword_lower in alias.lower():
                matched.append(standard_id)

        self._load_entity_cache()
        for entity in self._entity_cache or []:
            eid = entity["id"]
            name = entity.get("name", "")
            aliases = entity.get("aliases", [])

            check_terms = [name] + aliases + [eid]
            for term in check_terms:
                if term and (term.lower() in keyword_lower or keyword_lower in term.lower()):
                    if eid not in matched:
                        matched.append(eid)
                    break

        return matched

    def _step2_embedding_match(self, question: str) -> List[str]:
        self._load_entity_cache()
        if self._summary_embeddings is None or len(self._summary_embeddings) == 0:
            return []

        q_emb = self._embedder.encode_single(question)
        sims = self._embedder.cosine_similarity(q_emb, self._summary_embeddings)

        top_indices = np.argsort(sims)[::-1][:ENTITY_LINK_TOP_K]
        matched = []
        for idx in top_indices:
            if sims[idx] >= ENTITY_LINK_COSINE_THRESHOLD:
                matched.append(self._summary_ids[idx])

        return matched

    def link(self, question: str) -> List[str]:
        normalized = self._step0_llm_normalize(question)
        logger.debug("LLM 정규화: '%s' → '%s'", question, normalized)

        step1_ids = self._step1_aliases_match(normalized)
        logger.debug("aliases 매칭: %s", step1_ids)

        step2_ids = self._step2_embedding_match(normalized)
        logger.debug("임베딩 유사도 매칭: %s", step2_ids)

        all_ids: List[str] = []
        seen: set[str] = set()
        for eid in step1_ids + step2_ids:
            if eid not in seen:
                all_ids.append(eid)
                seen.add(eid)

        logger.info("링킹 결과: %d개 Entity %s", len(all_ids), all_ids)
        return all_ids
