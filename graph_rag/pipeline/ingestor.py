"""
graph_rag/pipeline/ingestor.py

역할:
- 추출된 엔티티·트리플·청크를 정규화 후 Kuzu DB에 적재한다.
- aliases 사전 적용 (표준 ID 변환)
- 중복 노드 감지 (동일 id → confidence 높은 속성 우선)
- confidence < 0.7 트리플 → review_queue 격리
- 청크 임베딩 생성 후 저장
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from graph_rag.config import ALIASES_MAP, CONFIDENCE_THRESHOLD
from graph_rag.db.graph_store import GraphStore
from graph_rag.schema.types import (
    ChunkLink, ChunkNode, EntityNode, Triple,
)

logger = logging.getLogger(__name__)


def _normalize_id(entity_id: str) -> str:
    """aliases 사전을 적용해 표준 ID로 변환한다."""
    return ALIASES_MAP.get(entity_id, entity_id)


class GraphIngestor:
    """정규화 + 그래프 DB 적재 담당."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    def ingest_chunks(self, chunks: List[ChunkNode]) -> None:
        """Chunk 노드를 임베딩과 함께 DB에 적재한다."""
        for chunk in chunks:
            self._store.upsert_chunk(chunk)
        logger.info("Chunk %d개 적재 완료", len(chunks))

    def ingest_entities(self, entities: List[EntityNode]) -> None:
        """aliases 정규화 후 Entity 노드를 DB에 적재한다."""
        seen: dict[str, EntityNode] = {}

        for entity in entities:
            # aliases 정규화
            entity.id = _normalize_id(entity.id)
            entity.aliases = [_normalize_id(a) for a in entity.aliases]

            # 중복 처리: confidence 높은 속성 유지
            if entity.id in seen:
                if entity.confidence > seen[entity.id].confidence:
                    seen[entity.id] = entity
            else:
                seen[entity.id] = entity

        for entity in seen.values():
            self._store.upsert_entity(entity)

        logger.info("Entity %d개 적재 완료 (중복 제거 후)", len(seen))

    def ingest_triples(self, triples: List[Triple]) -> None:
        """
        트리플을 적재한다.
        - subject_id, object_id에 aliases 정규화 적용
        - confidence < threshold → review_queue로 격리
        """
        low_conf = 0
        ingested = 0

        for triple in triples:
            triple.subject_id = _normalize_id(triple.subject_id)
            triple.object_id = _normalize_id(triple.object_id)

            if triple.confidence < CONFIDENCE_THRESHOLD:
                low_conf += 1
                # graph_store._add_to_review_queue 내부에서 처리
                self._store.upsert_triple(triple)
            else:
                self._store.upsert_triple(triple)
                ingested += 1

        logger.info(
            "Triple 적재 완료: %d건 적재, %d건 review_queue 격리",
            ingested, low_conf,
        )

    def ingest_chunk_links(self, links: List[Tuple[str, str]]) -> None:
        """(entity_id, chunk_id) 연결 목록을 ENTITY_FOUND_IN 엣지로 적재한다."""
        for entity_id, chunk_id in links:
            entity_id = _normalize_id(entity_id)
            link = ChunkLink(
                node_id=entity_id,
                node_type="Entity",
                chunk_id=chunk_id,
                link_type="FOUND_IN",
                confidence=1.0,
            )
            self._store.upsert_chunk_link(link)
        logger.info("ChunkLink %d개 적재 완료", len(links))

    def ingest_all(
        self,
        chunks: List[ChunkNode],
        entities: List[EntityNode],
        triples: List[Triple],
        chunk_links: List[Tuple[str, str]],
    ) -> None:
        """파이프라인 6단계를 순서대로 실행한다."""
        logger.info("=== 그래프 적재 시작 ===")
        self.ingest_chunks(chunks)
        self.ingest_entities(entities)
        self.ingest_triples(triples)
        self.ingest_chunk_links(chunk_links)
        logger.info("=== 그래프 적재 완료 ===")
