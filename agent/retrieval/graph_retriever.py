"""
agent/retrieval/graph_retriever.py

역할:
- Topic Entity 노드에서 출발하여 멀티홉 그래프 탐색을 수행한다.
- DDE(Directional Distance Encoding) 스코어링:
    홉 0 → 1.0, 홉 1 → 0.5, 홉 2 → 0.25, 홉 3 → 0.125
    트리플 점수 = (출발 노드 score + 도착 노드 score) / 2
- BLOCKS, ENABLES_SHORTCUT 엣지는 거리 무관 강제 포함 (K 제한 없음)
- 연결된 Chunk를 FOUND_IN 엣지로 수집하여 반환
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Dict, List, Set, Tuple

from graph_rag.config import (
    ALWAYS_INCLUDE_EDGE_TYPES, DDE_SCORE_BY_HOP,
    DEFAULT_HOP_DEPTH, TOP_K_GRAPH_DEFAULT,
)
from graph_rag.db.graph_store import GraphStore
from graph_rag.schema.types import ChunkNode, Triple

logger = logging.getLogger(__name__)


class DDEGraphRetriever:
    """DDE 스코어링 기반 멀티홉 그래프 탐색기."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    def retrieve(
        self,
        entity_ids: List[str],
        hop_depth: int = DEFAULT_HOP_DEPTH,
        top_k: int = TOP_K_GRAPH_DEFAULT,
    ) -> Tuple[List[dict], List[dict]]:
        """
        Args:
            entity_ids: 시작 Entity ID 목록
            hop_depth: 탐색 홉 깊이 (기본 2)
            top_k: 반환할 트리플 수 (강제 포함 엣지는 추가)

        Returns:
            (scored_triples, chunks)
            scored_triples: [{triple_dict, score}]
            chunks: [{id, text, source_file, ...}]
        """
        if not entity_ids:
            return [], []

        node_scores: Dict[str, float] = {}
        for eid in entity_ids:
            node_scores[eid] = 1.0

        all_edges: list[dict] = []
        visited: Set[str] = set(entity_ids)
        queue: deque[Tuple[str, int]] = deque([(eid, 0) for eid in entity_ids])

        while queue:
            node_id, hop = queue.popleft()
            if hop >= hop_depth:
                continue

            neighbors = self._store.get_neighbors(node_id, hop=1)
            for neighbor in neighbors:
                dst_id = neighbor["dst_id"]
                rel_type = neighbor["rel_type"]

                src_score = node_scores.get(neighbor["src_id"], 0.0)
                next_hop = hop + 1
                dst_score = DDE_SCORE_BY_HOP.get(next_hop, 0.0)

                if dst_id not in node_scores or dst_score > node_scores[dst_id]:
                    node_scores[dst_id] = dst_score

                edge_score = (src_score + dst_score) / 2
                all_edges.append({
                    "src_id": neighbor["src_id"],
                    "rel_type": rel_type,
                    "dst_id": dst_id,
                    "score": edge_score,
                    "hop": next_hop,
                })

                if dst_id not in visited:
                    visited.add(dst_id)
                    queue.append((dst_id, next_hop))

        forced_edges = [e for e in all_edges if e["rel_type"] in ALWAYS_INCLUDE_EDGE_TYPES]
        ranked_edges = sorted(
            [e for e in all_edges if e["rel_type"] not in ALWAYS_INCLUDE_EDGE_TYPES],
            key=lambda x: x["score"],
            reverse=True,
        )[:top_k]

        final_edges = forced_edges + ranked_edges
        logger.info(
            "그래프 탐색 완료: %d 노드 방문, 엣지 %d개 (강제포함 %d개)",
            len(visited), len(final_edges), len(forced_edges),
        )

        all_node_ids = list(visited)
        chunks = self._store.get_chunks_for_nodes(all_node_ids)

        return final_edges, chunks
