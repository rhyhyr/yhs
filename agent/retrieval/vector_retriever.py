"""
agent/retrieval/vector_retriever.py

역할:
- 그래프 탐색이 실패하거나 Chunk가 부족할 때 동작하는 Fallback 벡터 검색.
- 1차: Neo4j 네이티브 벡터 인덱스
- 2차: numpy 코사인 유사도 fallback
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

from graph_rag.config import TOP_K_VECTOR, USE_NEO4J_VECTOR_INDEX
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

logger = logging.getLogger(__name__)


class VectorRetriever:
    def __init__(self, store: GraphStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._chunk_ids: List[str] = []
        self._chunk_texts: List[str] = []
        self._chunk_meta: List[dict] = []
        self._matrix: Optional[np.ndarray] = None

    def _search_neo4j(self, question: str, top_k: int) -> List[dict]:
        q_emb = self._embedder.encode_single(question)
        raw = self._store.vector_search_chunks(q_emb, top_k)
        results = []
        for c in raw:
            results.append({
                "id": c.get("id", ""),
                "text": c.get("text", ""),
                "source_file": c.get("source_file", ""),
                "source_page": c.get("source_page", 0),
                "doc_version": c.get("doc_version", ""),
                "score": float(c.get("score", 0.0)),
            })
        return results

    def _build_index(self) -> None:
        raw = self._store.get_all_chunks_with_embeddings()
        valid = [c for c in raw if c.get("embedding")]

        if not valid:
            logger.warning("임베딩이 있는 Chunk가 없습니다. 벡터 검색 불가.")
            self._matrix = np.zeros((0, 1024), dtype=np.float32)
            return

        self._chunk_ids = [c["id"] for c in valid]
        self._chunk_texts = [c["text"] for c in valid]
        self._chunk_meta = [
            {k: v for k, v in c.items() if k not in ("embedding", "text")}
            for c in valid
        ]
        self._matrix = np.array([c["embedding"] for c in valid], dtype=np.float32)
        logger.info("numpy 벡터 인덱스 구축 완료: %d 청크", len(valid))

    def _search_numpy(self, question: str, top_k: int) -> List[dict]:
        if self._matrix is None:
            self._build_index()

        if self._matrix is None or len(self._matrix) == 0:
            return []

        q_emb = self._embedder.encode_single(question)
        sims = self._embedder.cosine_similarity(q_emb, self._matrix)

        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            meta = self._chunk_meta[idx].copy()
            meta["id"] = self._chunk_ids[idx]
            meta["text"] = self._chunk_texts[idx]
            meta["score"] = float(sims[idx])
            results.append(meta)
        return results

    def invalidate_index(self) -> None:
        self._matrix = None
        self._chunk_ids = []

    def search(self, question: str, top_k: int = TOP_K_VECTOR) -> List[dict]:
        results: List[dict] = []

        if USE_NEO4J_VECTOR_INDEX:
            try:
                results = self._search_neo4j(question, top_k)
                if results:
                    logger.info(
                        "Neo4j 벡터 검색 완료: %d개 반환 (top score=%.3f)",
                        len(results), results[0]["score"],
                    )
                    return results
                logger.debug("Neo4j 벡터 인덱스 결과 없음 → numpy fallback")
            except Exception as exc:
                logger.warning("Neo4j 벡터 검색 실패, numpy fallback 사용: %s", exc)

        results = self._search_numpy(question, top_k)
        if results:
            logger.info(
                "numpy 벡터 검색 완료: %d개 반환 (top score=%.3f)",
                len(results), results[0]["score"],
            )
        return results
