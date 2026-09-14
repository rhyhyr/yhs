"""
yhs/ingest/pipeline/ingestor.py

역할:
- 추출된 엔티티·트리플·청크를 정규화 후 Kuzu DB에 적재한다.
- aliases 사전 적용 (표준 ID 변환)
- 중복 노드 감지 (동일 id → confidence 높은 속성 우선)
- confidence < 0.7 트리플 → review_queue 격리
- 청크 임베딩 생성 후 저장
"""

from __future__ import annotations

import logging
import re

from yhs.core.config import ALIASES_MAP, CONFIDENCE_THRESHOLD
from yhs.infra.graph_store import GraphStore
from yhs.ingest.stats import STATS
from yhs.schema.types import (
    ChunkLink,
    ChunkNode,
    EntityNode,
    Triple,
)

logger = logging.getLogger(__name__)


def _normalize_id(entity_id: str) -> str:
    """aliases 사전을 적용해 표준 ID로 변환한다."""
    return ALIASES_MAP.get(entity_id, entity_id)


# 표준 비자/체류자격 코드 형태 (D-2, F-5, H-1 …). 이 형태의 id 는 그대로 쓴다.
_VISA_CODE_RE = re.compile(r"^[A-Z]-\d{1,2}$")

# id 로 쓸 수 없는 문자
_ID_STRIP_RE = re.compile(r"[^\w가-힣.-]+", re.UNICODE)


def _canonical_id(name: str, llm_id: str = "") -> str:
    """엔티티 이름에서 결정적 id 를 만든다.

    LLM 이 준 id 를 그대로 쓰면 안 되는 이유:
        추출 스키마의 예시("예: D-4")를 LLM 이 "문자-숫자 일련번호를 매기라"로
        해석해 청크마다 D-1, D-2 … E-1 … I-1 을 새로 발급했다. 그 결과
          - 비자 코드 이름공간이 오염됐다 (D-2 = '안내 동영상',
            D-4 = '임대차 계약서'). ALIASES_MAP 의 '유학비자'→'D-2' 가
            엉뚱한 노드를 가리켜, 모든 비자 질문이 검찰청 노드에서
            그래프 탐색을 시작했다.
          - 같은 기관이 여러 노드로 쪼개졌다
            ('수원지방검찰청 성남지청' = D-31, E-29, E-수원성남지청, I-9).
          - 매 실행마다 id 가 달라져 재인제스트가 멱등하지 않았다.

    이름에서 만들면 위 세 가지가 모두 사라지고, 같은 개념이 항상 한 노드로
    합쳐진다. id 가 사람이 읽을 수 있어 그래프 디버깅도 쉬워진다.
    """
    raw = (name or llm_id or "").strip()
    if not raw:
        return ""

    # 1) 별칭 사전에 있으면 표준 코드로 (유학비자 → D-2)
    if raw in ALIASES_MAP:
        return ALIASES_MAP[raw]

    # 2) 이미 표준 비자 코드 형태면 그대로
    if _VISA_CODE_RE.match(raw):
        return raw

    # 3) 그 외에는 이름을 슬러그로. 같은 이름 → 같은 id → 자동 병합.
    slug = _ID_STRIP_RE.sub("_", raw).strip("_")
    return slug[:80] or ""


class GraphIngestor:
    """정규화 + 그래프 DB 적재 담당."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store
        # LLM 이 준 id → 이름 기반 정규 id 매핑.
        # 엔티티 적재 때 만들고, 트리플·청크링크가 같은 매핑을 따라간다.
        self._id_map: dict[str, str] = {}
        # 실제로 적재된 엔티티 id. 관계를 저장하기 전에 양 끝이
        # 여기 있는지 확인한다.
        self._entity_ids: set[str] = set()

    def _resolve(self, raw_id: str) -> str:
        """LLM id 를 정규 id 로 바꾼다. 매핑에 없으면 별칭 정규화만 적용한다."""
        if raw_id in self._id_map:
            return self._id_map[raw_id]
        return _normalize_id(raw_id)

    def ingest_chunks(self, chunks: list[ChunkNode]) -> None:
        """Chunk 노드를 임베딩과 함께 DB에 적재한다."""
        for chunk in chunks:
            self._store.upsert_chunk(chunk)
        logger.info("Chunk %d개 적재 완료", len(chunks))

    def ingest_entities(self, entities: list[EntityNode]) -> None:
        """이름 기반 정규 id 를 부여한 뒤 Entity 노드를 DB에 적재한다."""
        seen: dict[str, EntityNode] = {}

        for entity in entities:
            canonical = _canonical_id(entity.name, entity.id)
            if not canonical:
                continue

            # 트리플·청크링크가 따라올 수 있도록 매핑을 남긴다.
            if entity.id:
                self._id_map[entity.id] = canonical

            entity.id = canonical
            entity.aliases = [_normalize_id(a) for a in entity.aliases]

            # 같은 정규 id 가 여러 번 나오면 confidence 높은 쪽을 남긴다.
            # (이름이 같은 엔티티가 여기서 한 노드로 합쳐진다)
            if canonical in seen:
                if entity.confidence > seen[canonical].confidence:
                    seen[canonical] = entity
            else:
                seen[canonical] = entity

        for entity in seen.values():
            self._store.upsert_entity(entity)
            self._entity_ids.add(entity.id)

        STATS.merged_entities += len(seen)
        STATS.dropped_entities += sum(
            1 for e in entities if not _canonical_id(e.name, e.id)
        )
        logger.info(
            "Entity %d개 적재 완료 (입력 %d개 → 이름 기준 병합 후 %d개)",
            len(seen), len(entities), len(seen),
        )

    def ingest_triples(self, triples: list[Triple]) -> None:
        """
        트리플을 적재한다.
        - subject_id, object_id 를 정규 id 로 해석
        - 양 끝 엔티티가 실재하는지 **미리** 확인한다
        - confidence < threshold → review_queue로 격리

        왜 미리 확인하는가:
            graph_store.upsert_triple 은 `MATCH (a:Entity{id})...MATCH (b...)`
            로 양 끝을 찾는다. 하나라도 없으면 MATCH 가 0행이 되고 MERGE 가
            실행되지 않는데, 빈 결과는 예외가 아니라 except 블록도 타지 않는다.
            즉 관계가 로그 한 줄 없이 사라진다. 실측으로 표본 21청크에서
            LLM 관계 169개 중 152개(90%)가 이렇게 유실됐다.
        """
        low_conf = 0
        ingested = 0
        missing = 0

        for triple in triples:
            triple.subject_id = self._resolve(triple.subject_id)
            triple.object_id = self._resolve(triple.object_id)

            # 양 끝이 실재하는지 확인. 없으면 건너뛰되 흔적을 남긴다.
            # 임의로 엔티티를 만들지는 않는다 — LLM 이 지어낸 문자열까지
            # 노드가 되면 그래프가 쓰레기로 찬다.
            miss = [
                nid for nid in (triple.subject_id, triple.object_id)
                if nid not in self._entity_ids
            ]
            if miss:
                missing += 1
                STATS.relation_match_failed += 1
                if len(STATS.match_failed_samples) < 20:
                    STATS.match_failed_samples.append(
                        f"{triple.subject_id} -[{triple.predicate}]-> "
                        f"{triple.object_id}  (없는 엔티티: {', '.join(miss)})"
                    )
                logger.warning(
                    "관계 저장 불가 — 엔티티 없음: %s -[%s]-> %s (없음: %s)",
                    triple.subject_id, triple.predicate, triple.object_id,
                    ", ".join(miss),
                )
                continue

            if triple.confidence < CONFIDENCE_THRESHOLD:
                low_conf += 1
                # graph_store._add_to_review_queue 내부에서 처리
                self._store.upsert_triple(triple)
            else:
                self._store.upsert_triple(triple)
                ingested += 1
                STATS.stored_relations += 1

        logger.info(
            "Triple 적재 완료: %d건 적재, %d건 review_queue 격리, "
            "%d건 엔티티 부재로 건너뜀",
            ingested, low_conf, missing,
        )

    def ingest_chunk_links(self, links: list[tuple[str, str]]) -> None:
        """(entity_id, chunk_id) 연결 목록을 ENTITY_FOUND_IN 엣지로 적재한다."""
        for entity_id, chunk_id in links:
            entity_id = self._resolve(entity_id)
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
        chunks: list[ChunkNode],
        entities: list[EntityNode],
        triples: list[Triple],
        chunk_links: list[tuple[str, str]],
    ) -> None:
        """파이프라인 6단계를 순서대로 실행한다."""
        logger.info("=== 그래프 적재 시작 ===")
        self.ingest_chunks(chunks)
        # 엔티티를 먼저 적재해야 _id_map 이 채워지고,
        # 트리플·청크링크가 같은 정규 id 를 따라갈 수 있다.
        self.ingest_entities(entities)
        self.ingest_triples(triples)
        self.ingest_chunk_links(chunk_links)
        logger.info("=== 그래프 적재 완료 ===")
