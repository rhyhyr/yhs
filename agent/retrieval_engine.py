"""
agent/retrieval_engine.py

역할:
- 3단계 계층 검색을 오케스트레이션한다.

    1단계 (그래프 탐색):
        Entity 링킹 성공 → DDE 스코어 그래프 탐색 → Chunk 수집
        Chunk가 MIN_CHUNKS_FROM_GRAPH(2)개 미만이면 2단계로 이어짐

    2단계 (벡터 Fallback):
        임베딩 유사도 Top-5 Chunk 반환

    3단계 ("모름" 응답):
        1·2단계 모두 실패 → NO_ANSWER_RESPONSE 반환

- 반환 전 신선도 경고 문구(만료 6개월 이상 Chunk)를 자동 삽입한다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from graph_rag.config import (
    DEFAULT_HOP_DEPTH,
    DISCLAIMER_TEMPLATE,
    DOC_STALENESS_MONTHS,
    MIN_CHUNKS_FROM_GRAPH,
    NO_ANSWER_RESPONSE,
    TOP_K_GRAPH_DEFAULT,
)
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder
from agent.retrieval.graph_retriever import DDEGraphRetriever
from agent.retrieval.linker import EntityLinker
from agent.retrieval.vector_retriever import VectorRetriever
from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)


def _is_stale(doc_version: str, months: int = DOC_STALENESS_MONTHS) -> bool:
    """doc_version(YYYY.MM 형식)이 기준 개월 이상 경과했으면 True를 반환한다."""
    if not doc_version:
        return False
    try:
        parts = doc_version.replace("-", ".").split(".")
        year, month = int(parts[0]), int(parts[1])
        doc_date = datetime(year, month, 1)
        return datetime.now() - doc_date > timedelta(days=30 * months)
    except (ValueError, IndexError):
        return False


def _build_disclaimer(source_file: str, doc_version: str) -> str:
    return DISCLAIMER_TEMPLATE.format(source_file=source_file, doc_version=doc_version)


class RetrievalEngine:
    """3단계 계층 검색 오케스트레이터."""

    def __init__(self, store: GraphStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder
        self._linker = EntityLinker(store, embedder)
        self._graph_retriever = DDEGraphRetriever(store)
        self._vector_retriever = VectorRetriever(store, embedder)

    def invalidate_caches(self) -> None:
        """새 데이터 인제스트 후 내부 캐시를 모두 무효화한다."""
        self._linker.invalidate_cache()
        self._vector_retriever.invalidate_index()

    def retrieve(
        self,
        question: str,
        hop_depth: int = DEFAULT_HOP_DEPTH,
        top_k: int = TOP_K_GRAPH_DEFAULT,
    ) -> RetrievalResult:
        """질문에 대한 검색 결과를 반환한다."""
        entity_ids = self._linker.link(question)
        triples: list = []
        chunks_raw: list = []

        if entity_ids:
            edges, chunks_raw = self._graph_retriever.retrieve(
                entity_ids, hop_depth=hop_depth, top_k=top_k
            )
            triples = edges

        if len(chunks_raw) >= MIN_CHUNKS_FROM_GRAPH:
            return self._build_result(triples, chunks_raw, "graph", entity_ids)

        logger.info("그래프 검색 Chunk 부족(%d개), 벡터 Fallback 실행", len(chunks_raw))

        vector_chunks = self._vector_retriever.search(question)
        if vector_chunks:
            return self._build_result([], vector_chunks, "vector", entity_ids)

        logger.info("검색 결과 없음 → '모름' 응답 반환")
        return RetrievalResult(
            triples=[],
            chunks=[],
            retrieval_method="no_answer",
            entity_ids=entity_ids,
        )

    def _build_result(
        self,
        triples: list,
        chunks_raw: list,
        method: str,
        entity_ids: List[str],
    ) -> RetrievalResult:
        from graph_rag.schema.types import ChunkNode

        chunk_nodes: List[ChunkNode] = []
        for c in chunks_raw:
            chunk_nodes.append(ChunkNode(
                id=c.get("id", ""),
                text=c.get("text", ""),
                source_file=c.get("source_file", ""),
                source_page=c.get("source_page", 0),
                doc_version=c.get("doc_version", ""),
            ))
        return RetrievalResult(
            triples=triples,
            chunks=chunk_nodes,
            retrieval_method=method,
            entity_ids=entity_ids,
        )

    def build_prompt_context(self, result: RetrievalResult) -> str:
        """검색 결과를 LLM 프롬프트용 컨텍스트 문자열로 변환한다."""
        if result.retrieval_method == "no_answer":
            return ""

        lines: List[str] = []

        if result.triples:
            lines.append("[그래프 트리플]")
            for t in result.triples[:15]:
                lines.append(f"({t.get('src_id', '')}, {t.get('rel_type', '')}, {t.get('dst_id', '')})")
            lines.append("")

        if result.chunks:
            lines.append("[원문]")
            for chunk in result.chunks[:5]:
                lines.append(f"{chunk.id}: \"{chunk.text[:400]}\"")
                if chunk.doc_version and _is_stale(chunk.doc_version):
                    lines.append(_build_disclaimer(chunk.source_file, chunk.doc_version))
            lines.append("")

        sources = {
            f"{c.source_file} ({c.doc_version})"
            for c in result.chunks
            if c.source_file
        }
        if sources:
            lines.append(f"[출처] {', '.join(sources)}")

        return "\n".join(lines)
