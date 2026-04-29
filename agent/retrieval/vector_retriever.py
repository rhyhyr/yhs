"""
agent/retrieval/vector_retriever.py

역할:
- 그래프 탐색이 실패하거나 Chunk가 부족할 때 동작하는 벡터 검색.
- 1차: Neo4j 네이티브 벡터 인덱스
- 2차: numpy 코사인 유사도 fallback

스코어링:
  hybrid_score = 0.65 * cosine + 0.25 * keyword_overlap + 0.10 * recency

  keyword_overlap = 0.6 * anchor_hit_rate + 0.4 * term_overlap_rate
  recency = 1.0 → 0개월, 0.0 → 24개월+
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import numpy as np

from graph_rag.config import TOP_K_VECTOR, USE_NEO4J_VECTOR_INDEX
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

logger = logging.getLogger(__name__)

# 하이브리드 스코어 가중치
_W_COS = 0.65
_W_KW  = 0.25
_W_REC = 0.10

# numpy fallback에서 cosine top-k 이후 재랭크할 후보 배수
_CANDIDATE_MULTIPLIER = 3


class VectorRetriever:
    def __init__(self, store: GraphStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._chunk_ids: List[str] = []
        self._chunk_texts: List[str] = []
        self._chunk_meta: List[dict] = []
        self._matrix: Optional[np.ndarray] = None

    # ── 스코어 헬퍼 ──────────────────────────────────────────────────────────
    def _keyword_overlap_score(
        self, text: str, question: str, keywords: list[str]
    ) -> float:
        """앵커/키워드 히트율 + 질문 단어 겹침을 결합한 점수 (0~1)."""
        t_lower = text.lower()
        q_lower = question.lower()

        if keywords:
            anchor_hits = sum(1 for kw in keywords if kw.lower() in t_lower)
            anchor_score = min(anchor_hits / len(keywords), 1.0)
        else:
            anchor_score = 0.0

        q_terms = {t for t in q_lower.split() if len(t) > 1}
        t_terms = {t for t in t_lower.split() if len(t) > 1}
        term_overlap = len(q_terms & t_terms) / max(len(q_terms), 1) if q_terms else 0.0

        return 0.6 * anchor_score + 0.4 * term_overlap

    def _recency_score(self, doc_version: str) -> float:
        """문서 최신성 점수 (0개월 → 1.0, 24개월+ → 0.0)."""
        if not doc_version:
            return 0.5
        try:
            parts = doc_version.replace("-", ".").split(".")
            year, month = int(parts[0]), int(parts[1])
            doc_date = datetime(year, month, 1)
            months_old = max(0, (datetime.now() - doc_date).days / 30)
            return max(0.0, 1.0 - months_old / 24.0)
        except (ValueError, IndexError):
            return 0.5

    def _hybrid_score(
        self, cosine: float, text: str, question: str,
        keywords: list[str], doc_version: str,
    ) -> float:
        kw  = self._keyword_overlap_score(text, question, keywords)
        rec = self._recency_score(doc_version)
        return _W_COS * cosine + _W_KW * kw + _W_REC * rec

    # ── Neo4j 벡터 검색 ──────────────────────────────────────────────────────
    def _search_neo4j(
        self, question: str, top_k: int, keywords: list[str]
    ) -> List[dict]:
        q_emb = self._embedder.encode_single(question)
        raw = self._store.vector_search_chunks(q_emb, top_k)
        results = []
        for c in raw:
            cosine = float(c.get("score", 0.0))
            text = c.get("text", "")
            doc_ver = c.get("doc_version", "")
            hybrid = self._hybrid_score(cosine, text, question, keywords, doc_ver)
            results.append({
                "id": c.get("id", ""),
                "text": text,
                "source_file": c.get("source_file", ""),
                "source_page": c.get("source_page", 0),
                "section": c.get("section", ""),
                "doc_version": doc_ver,
                "score": hybrid,
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
    ) -> List[dict]:
        if self._matrix is None:
            self._build_index()

        if self._matrix is None or len(self._matrix) == 0:
            return []

        q_emb = self._embedder.encode_single(question)
        sims = self._embedder.cosine_similarity(q_emb, self._matrix)

        # cosine 기준으로 후보를 더 뽑은 뒤 하이브리드 스코어로 재랭크
        candidate_k = min(top_k * _CANDIDATE_MULTIPLIER, len(sims))
        top_indices = np.argsort(sims)[::-1][:candidate_k]

        results = []
        for idx in top_indices:
            cosine = float(sims[idx])
            text = self._chunk_texts[idx]
            meta = self._chunk_meta[idx]
            doc_ver = meta.get("doc_version", "")
            hybrid = self._hybrid_score(cosine, text, question, keywords, doc_ver)

            entry = meta.copy()
            entry["id"] = self._chunk_ids[idx]
            entry["text"] = text
            entry["score"] = hybrid
            results.append(entry)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

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
    ) -> List[dict]:
        """하이브리드 스코어(cosine + keyword + recency) 기반 청크 검색."""
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
