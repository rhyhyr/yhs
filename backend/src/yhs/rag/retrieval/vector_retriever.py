"""
yhs/rag/retrieval/vector_retriever.py

역할:
- 그래프 탐색이 실패하거나 Chunk가 부족할 때 동작하는 벡터 검색.
- 1차: Neo4j 네이티브 벡터 인덱스
- 2차: numpy 코사인 유사도 fallback

스코어링:
  순수 코사인 유사도만 반환. 키워드·최신성 혼합은 retrieval_engine._merge_and_rerank()
  에서 한 번만 수행한다 (여기서 섞으면 engine에서 이중 계산됨).
"""

from __future__ import annotations

import logging

import numpy as np

from yhs.core.config import TOP_K_VECTOR, USE_NEO4J_VECTOR_INDEX
from yhs.infra.embedder import Embedder
from yhs.infra.graph_store import GraphStore

logger = logging.getLogger(__name__)

# numpy fallback에서 cosine top-k 후보 배수 (retrieval_engine이 최종 재랭크)
_CANDIDATE_MULTIPLIER = 3


class VectorRetriever:
    def __init__(self, store: GraphStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._chunk_ids: list[str] = []
        self._chunk_texts: list[str] = []
        self._chunk_meta: list[dict] = []
        self._matrix: np.ndarray | None = None

    # ── Neo4j 벡터 검색 ──────────────────────────────────────────────────────
    def _search_neo4j(
        self, question: str, top_k: int, keywords: list[str]
    ) -> list[dict]:
        q_emb = self._embedder.encode_single(question)
        raw = self._store.vector_search_chunks(q_emb, top_k)
        results = []
        for c in raw:
            results.append({
                "id": c.get("id", ""),
                "text": c.get("text", ""),
                "source_file": c.get("source_file", ""),
                "source_page": c.get("source_page", 0),
                "section": c.get("section", ""),
                "doc_version": c.get("doc_version", ""),
                "score": float(c.get("score", 0.0)),  # 순수 코사인
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # ── numpy fallback 인덱스 ─────────────────────────────────────────────────
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

    def _search_numpy(
        self, question: str, top_k: int, keywords: list[str]
    ) -> list[dict]:
        if self._matrix is None:
            self._build_index()

        if self._matrix is None or len(self._matrix) == 0:
            return []

        q_emb = self._embedder.encode_single(question)
        sims = self._embedder.cosine_similarity(q_emb, self._matrix)

        candidate_k = min(top_k * _CANDIDATE_MULTIPLIER, len(sims))
        top_indices = np.argsort(sims)[::-1][:candidate_k]

        results = []
        for idx in top_indices:
            entry = self._chunk_meta[idx].copy()
            entry["id"] = self._chunk_ids[idx]
            entry["text"] = self._chunk_texts[idx]
            entry["score"] = float(sims[idx])  # 순수 코사인
            results.append(entry)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _get_all_chunks(self) -> list[dict]:
        """인덱스에 있는 모든 청크를 id/text/meta dict 리스트로 반환한다 (소스 라우팅용)."""
        if self._matrix is None:
            self._build_index()
        results = []
        for i, cid in enumerate(self._chunk_ids):
            entry = self._chunk_meta[i].copy()
            entry["id"] = cid
            entry["text"] = self._chunk_texts[i]
            results.append(entry)
        return results

    # ── 캐시 무효화 ──────────────────────────────────────────────────────────
    def invalidate_index(self) -> None:
        self._matrix = None
        self._chunk_ids = []
        self._chunk_texts = []
        self._chunk_meta = []

    # ── 메인 검색 ────────────────────────────────────────────────────────────
    def search(
        self,
        question: str,
        top_k: int = TOP_K_VECTOR,
        keywords: list[str] | None = None,
    ) -> list[dict]:
        """코사인 유사도 기반 청크 검색. 키워드·최신성 혼합은 retrieval_engine에서 수행."""
        if keywords is None:
            keywords = []

        if USE_NEO4J_VECTOR_INDEX:
            try:
                # 재랭크를 위해 top_k보다 넉넉하게 가져온다
                results = self._search_neo4j(question, top_k * 2, keywords)
                if results:
                    logger.info(
                        "Neo4j 벡터 검색 완료: %d개 반환 (top score=%.3f)",
                        len(results[:top_k]), results[0]["score"],
                    )
                    return results[:top_k]
                logger.debug("Neo4j 벡터 인덱스 결과 없음 → numpy fallback")
            except Exception as exc:
                logger.warning("Neo4j 벡터 검색 실패, numpy fallback 사용: %s", exc)

        results = self._search_numpy(question, top_k, keywords)
        if results:
            logger.info(
                "numpy 벡터 검색 완료: %d개 반환 (top score=%.3f)",
                len(results), results[0]["score"],
            )
        return results
