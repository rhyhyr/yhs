"""
yhs/rag/retrieval/graph_retriever.py

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

from yhs.core.config import (
    ALWAYS_INCLUDE_EDGE_TYPES,
    DDE_SCORE_BY_HOP,
    DEFAULT_HOP_DEPTH,
    TOP_K_GRAPH_DEFAULT,
    TRAVERSAL_EXCLUDE_EDGE_TYPES,
)
from yhs.infra.graph_store import GraphStore

logger = logging.getLogger(__name__)


class DDEGraphRetriever:
    """DDE 스코어링 기반 멀티홉 그래프 탐색기."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    def retrieve(
        self,
        entity_ids: list[str],
        hop_depth: int = DEFAULT_HOP_DEPTH,
        top_k: int = TOP_K_GRAPH_DEFAULT,
    ) -> tuple[list[dict], list[dict]]:
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

        node_scores: dict[str, float] = {}
        for eid in entity_ids:
            node_scores[eid] = 1.0

        all_edges: list[dict] = []
        visited: set[str] = set(entity_ids)
        queue: deque[tuple[str, int]] = deque([(eid, 0) for eid in entity_ids])

        while queue:
            node_id, hop = queue.popleft()
            if hop >= hop_depth:
                continue

            neighbors = self._store.get_neighbors(node_id, hop=1)
            for neighbor in neighbors:
                dst_id = neighbor["dst_id"]
                rel_type = neighbor["rel_type"]

                # 포괄 술어(RELATED_TO 등)는 따라 걷지 않는다.
                # 의미가 옅은데 팬아웃이 커서 그래프를 전수 스캔으로 만든다.
                if rel_type in TRAVERSAL_EXCLUDE_EDGE_TYPES:
                    continue

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

        # 청크는 "선택된 엣지에 등장한 노드" 에서만 가져온다.
        #
        # 예전에는 visited 전체에서 가져왔다. 엣지는 top_k 로 걸러 놓고 노드는
        # 안 걸렀기 때문에, hop=2 만 돌아도 KB 의 69% 가 후보로 쏟아졌다
        # (엣지 103개 → 청크 236개, 전체 342개 중). 그래프가 좁혀 주는 역할을
        # 전혀 못 하고 실제 선별은 키워드 점수가 다 하고 있었다.
        selected_nodes: set[str] = set(entity_ids)
        for edge in final_edges:
            selected_nodes.add(edge["src_id"])
            selected_nodes.add(edge["dst_id"])

        chunks = self._store.get_chunks_for_nodes(list(selected_nodes))
        logger.info(
            "그래프 청크 수집: 방문 노드 %d개 중 선택 %d개 → 청크 %d개",
            len(visited), len(selected_nodes), len(chunks),
        )

        for chunk in chunks:
            source_node_ids = chunk.pop("source_node_ids", None) or []
            chunk["_graph_score"] = max(
                (node_scores.get(nid, 0.0) for nid in source_node_ids),
                default=0.0,
            )

        return final_edges, chunks
