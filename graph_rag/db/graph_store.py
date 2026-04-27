"""
graph_rag/db/graph_store.py

역할:
- Neo4j DB 연결 및 스키마 초기화 (제약·인덱스).
- 노드/엣지 CRUD (MERGE 패턴으로 upsert).
- Neo4j 5.11+ 네이티브 벡터 인덱스를 통한 Chunk 유사도 검색.
- review_queue (낮은 confidence 트리플 격리) JSON 파일 관리.
- 신선도 플래그(needs_review) 일괄 업데이트.

Neo4j 장점 (Kuzu 대비):
  - 관계 타입에 FROM/TO 노드 타입 제약 없음 → FOUND_IN·BLOCKS 등 다형 관계 자유롭게 사용
  - 네이티브 벡터 인덱스(5.11+)로 임베딩을 DB 내부에서 바로 검색
  - 기존 프로젝트(hybrid_query_agent.py)와 동일한 인프라 재사용 가능
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, List, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ClientError, ServiceUnavailable

from graph_rag.config import (
    CONFIDENCE_THRESHOLD,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    REVIEW_QUEUE_PATH,
    USE_NEO4J_VECTOR_INDEX,
    EMBEDDING_DIM,
)
from graph_rag.schema.types import (
    ChunkLink, ChunkNode, DocumentNode, DomainNode,
    EntityNode, InstitutionNode, ProcedureNode, TopicNode, Triple,
)

logger = logging.getLogger(__name__)

# ─── 스키마 초기화 쿼리 ───────────────────────────────────────────────────────
_CONSTRAINTS = [
    "CREATE CONSTRAINT entity_id    IF NOT EXISTS FOR (n:Entity)      REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id     IF NOT EXISTS FOR (n:Chunk)       REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT domain_id    IF NOT EXISTS FOR (n:Domain)      REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT topic_id     IF NOT EXISTS FOR (n:Topic)       REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT procedure_id IF NOT EXISTS FOR (n:Procedure)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT document_id  IF NOT EXISTS FOR (n:Document)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT inst_id      IF NOT EXISTS FOR (n:Institution) REQUIRE n.id IS UNIQUE",
]

_INDEXES = [
    "CREATE INDEX entity_domain  IF NOT EXISTS FOR (n:Entity)  ON (n.domain)",
    "CREATE INDEX entity_name    IF NOT EXISTS FOR (n:Entity)  ON (n.name)",
    "CREATE INDEX chunk_src      IF NOT EXISTS FOR (n:Chunk)   ON (n.source_file)",
    "CREATE INDEX chunk_ver      IF NOT EXISTS FOR (n:Chunk)   ON (n.doc_version)",
]

# Neo4j 5.11+ 벡터 인덱스 (USE_NEO4J_VECTOR_INDEX=true 일 때만 생성)
_VECTOR_INDEX_QUERY = f"""
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {{indexConfig: {{
    `vector.dimensions`: {EMBEDDING_DIM},
    `vector.similarity_function`: 'cosine'
}}}}
"""


class GraphStore:
    """Neo4j 그래프 DB 연결 및 데이터 접근 레이어."""

    def __init__(
        self,
        uri: str = NEO4J_URI,
        user: str = NEO4J_USER,
        password: str = NEO4J_PASSWORD,
        database: str = NEO4J_DATABASE,
    ) -> None:
        if not password:
            raise ValueError(
                "NEO4J_PASSWORD가 설정되지 않았습니다. "
                ".env 파일에 NEO4J_PASSWORD=<비밀번호>를 추가하세요."
            )
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database
        self._init_schema()
        logger.info("GraphStore(Neo4j) 초기화 완료: %s / db=%s", uri, database)

    # ─── 스키마 초기화 ────────────────────────────────────────────────────────
    def _init_schema(self) -> None:
        with self._driver.session(database=self._database) as s:
            for q in _CONSTRAINTS:
                try:
                    s.run(q)
                except ClientError as e:
                    logger.debug("제약 생성 스킵 (이미 존재): %s", e)

            for q in _INDEXES:
                try:
                    s.run(q)
                except ClientError as e:
                    logger.debug("인덱스 생성 스킵: %s", e)

            if USE_NEO4J_VECTOR_INDEX:
                try:
                    s.run(_VECTOR_INDEX_QUERY)
                    logger.info("벡터 인덱스(chunk_embedding) 생성/확인 완료")
                except ClientError as e:
                    logger.warning("벡터 인덱스 생성 실패 (Neo4j 5.11+ 필요): %s", e)

    # ─── 내부 실행 헬퍼 ──────────────────────────────────────────────────────
    def _run(self, query: str, **params: Any) -> list[dict]:
        with self._driver.session(database=self._database) as s:
            result = s.run(query, **params)
            return [dict(r) for r in result]

    def _run_write(self, query: str, **params: Any) -> None:
        with self._driver.session(database=self._database) as s:
            s.run(query, **params)

    # ─── 노드 Upsert ─────────────────────────────────────────────────────────
    def upsert_domain(self, node: DomainNode) -> None:
        self._run_write(
            "MERGE (n:Domain {id: $id}) SET n.name = $name, n.updated_at = $now",
            id=node.id, name=node.name, now=_now(),
        )

    def upsert_topic(self, node: TopicNode) -> None:
        self._run_write(
            "MERGE (n:Topic {id: $id}) SET n.name = $name, n.domain = $domain, n.updated_at = $now",
            id=node.id, name=node.name, domain=node.domain, now=_now(),
        )

    def upsert_entity(self, node: EntityNode) -> None:
        # 기존 노드가 있으면 confidence가 높은 속성만 유지
        existing = self._run(
            "MATCH (n:Entity {id: $id}) RETURN n.confidence AS c", id=node.id
        )
        if existing and existing[0]["c"] is not None:
            if node.confidence < existing[0]["c"]:
                return

        self._run_write(
            """
            MERGE (n:Entity {id: $id})
            SET n.name          = $name,
                n.domain        = $domain,
                n.aliases       = $aliases,
                n.summary       = $summary,
                n.valid_from    = $valid_from,
                n.valid_until   = $valid_until,
                n.last_verified = $last_verified,
                n.confidence    = $confidence,
                n.source        = $source,
                n.needs_review  = $needs_review,
                n.updated_at    = $now
            """,
            id=node.id,
            name=node.name,
            domain=node.domain,
            aliases=node.aliases,
            summary=node.summary,
            valid_from=node.valid_from or "",
            valid_until=node.valid_until or "",
            last_verified=node.last_verified or "",
            confidence=node.confidence,
            source=node.source,
            needs_review=node.needs_review,
            now=_now(),
        )

    def upsert_procedure(self, node: ProcedureNode) -> None:
        self._run_write(
            """
            MERGE (n:Procedure {id: $id})
            SET n.name         = $name,
                n.step_order   = $step_order,
                n.parent_proc  = $parent_proc,
                n.description  = $description,
                n.duration_est = $duration_est,
                n.domain       = $domain,
                n.updated_at   = $now
            """,
            id=node.id, name=node.name, step_order=node.step_order,
            parent_proc=node.parent_proc, description=node.description,
            duration_est=node.duration_est, domain=node.domain, now=_now(),
        )

    def upsert_document(self, node: DocumentNode) -> None:
        self._run_write(
            "MERGE (n:Document {id: $id}) SET n.name=$name, n.domain=$domain, n.updated_at=$now",
            id=node.id, name=node.name, domain=node.domain, now=_now(),
        )

    def upsert_institution(self, node: InstitutionNode) -> None:
        self._run_write(
            "MERGE (n:Institution {id: $id}) SET n.name=$name, n.domain=$domain, n.updated_at=$now",
            id=node.id, name=node.name, domain=node.domain, now=_now(),
        )

    def upsert_chunk(self, node: ChunkNode) -> None:
        """
        Chunk 노드를 upsert한다.
        embedding은 Neo4j 5.11+ 벡터 인덱스와 호환되는 float 리스트로 저장한다.
        """
        self._run_write(
            """
            MERGE (n:Chunk {id: $id})
            SET n.text         = $text,
                n.embedding    = $embedding,
                n.source_file  = $source_file,
                n.source_page  = $source_page,
                n.section      = $section,
                n.language     = $language,
                n.doc_version  = $doc_version,
                n.needs_review = $needs_review,
                n.created_at   = coalesce(n.created_at, $now)
            """,
            id=node.id,
            text=node.text,
            embedding=node.embedding or [],   # float list → Neo4j LIST<FLOAT>
            source_file=node.source_file,
            source_page=node.source_page,
            section=node.section,
            language=node.language,
            doc_version=node.doc_version,
            needs_review=node.needs_review,
            now=_now(),
        )

    # ─── 엣지 Upsert ─────────────────────────────────────────────────────────
    def upsert_triple(self, triple: Triple) -> None:
        """
        Triple을 Neo4j 관계로 적재한다.
        - Neo4j는 FROM/TO 타입 제약이 없으므로 BLOCKS·RELATED_TO 등 다형 관계를 그대로 사용한다.
        - confidence < 임계값이면 review_queue에 격리한다.
        """
        if triple.confidence < CONFIDENCE_THRESHOLD:
            self._add_to_review_queue(triple)
            return

        p = triple.predicate
        base_props = {
            "confidence": triple.confidence,
            "source": triple.source,
            "source_page": triple.source_page,
            "verified": triple.verified,
            "created_at": triple.created_at,
        }

        # predicate별 추가 속성
        extra: dict = {}
        if p == "CAN_TRANSITION_TO":
            extra = {"condition": triple.condition}
        elif p == "REQUIRES":
            extra = {"mandatory": triple.mandatory}
        elif p == "BLOCKS":
            extra = {"block_reason": triple.block_reason}
        elif p == "NEXT_STEP":
            extra = {"step_order": triple.step_order}
        elif p == "ENABLES_SHORTCUT":
            extra = {"skip_to": triple.skip_to}
        elif p == "RELATED_TO":
            extra = {"relation_desc": triple.relation_desc}

        props = {**base_props, **extra}

        # Neo4j는 라벨을 몰라도 id로 MATCH 가능
        query = f"""
        MATCH (a {{id: $s}}), (b {{id: $o}})
        MERGE (a)-[r:{p}]->(b)
        SET r += $props
        """
        try:
            self._run_write(query, s=triple.subject_id, o=triple.object_id, props=props)
        except Exception as exc:
            logger.error("triple 적재 실패 (%s -[%s]-> %s): %s",
                         triple.subject_id, p, triple.object_id, exc)

    def upsert_chunk_link(self, link: ChunkLink) -> None:
        """
        구조 노드 → Chunk 연결 (FOUND_IN / MENTIONED_IN).
        Neo4j는 라벨 무관하게 id로 MATCH하므로 단일 쿼리로 처리한다.
        """
        query = f"""
        MATCH (a {{id: $nid}}), (b:Chunk {{id: $cid}})
        MERGE (a)-[r:{link.link_type}]->(b)
        SET r.confidence = $conf,
            r.source     = $src,
            r.created_at = $now
        """
        try:
            self._run_write(
                query,
                nid=link.node_id, cid=link.chunk_id,
                conf=link.confidence, src=link.source, now=_now(),
            )
        except Exception as exc:
            logger.error("chunk link 적재 실패: %s", exc)

    # ─── 조회 ────────────────────────────────────────────────────────────────
    def get_all_entities_summary(self) -> list[dict]:
        """Entity 링킹용: 모든 Entity의 id, name, aliases, summary, domain 반환."""
        rows = self._run(
            "MATCH (n:Entity) RETURN n.id AS id, n.name AS name, "
            "n.aliases AS aliases, n.summary AS summary, n.domain AS domain"
        )
        return rows

    def get_all_chunks_with_embeddings(self) -> list[dict]:
        """numpy 벡터 검색용: embedding이 있는 모든 Chunk 반환."""
        rows = self._run(
            "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL AND size(c.embedding) > 0 "
            "RETURN c.id AS id, c.text AS text, c.embedding AS embedding, "
            "c.source_file AS source_file, c.source_page AS source_page, "
            "c.section AS section, c.language AS language, "
            "c.doc_version AS doc_version, c.needs_review AS needs_review"
        )
        return rows

    def vector_search_chunks(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict]:
        """
        Neo4j 5.11+ 네이티브 벡터 인덱스를 사용한 Chunk 유사도 검색.
        USE_NEO4J_VECTOR_INDEX=false 이거나 인덱스가 없으면 빈 목록 반환
        (vector_retriever.py의 numpy fallback이 처리).
        """
        if not USE_NEO4J_VECTOR_INDEX:
            return []
        try:
            rows = self._run(
                """
                CALL db.index.vector.queryNodes('chunk_embedding', $k, $emb)
                YIELD node, score
                RETURN node.id        AS id,
                       node.text      AS text,
                       node.source_file AS source_file,
                       node.source_page AS source_page,
                       node.doc_version AS doc_version,
                       score
                """,
                k=top_k, emb=query_embedding,
            )
            return rows
        except ClientError as exc:
            logger.warning("네이티브 벡터 검색 실패 (numpy fallback 사용): %s", exc)
            return []

    def get_neighbors(self, entity_id: str, hop: int = 2) -> list[dict]:
        """entity_id에서 hop 거리 내 모든 관계(엣지)를 반환한다."""
        query = f"""
        MATCH path = (src {{id: $id}})-[r*1..{hop}]-(dst)
        WITH relationships(path)[-1] AS last_r,
             nodes(path)[0]         AS src_node,
             nodes(path)[-1]        AS dst_node
        RETURN src_node.id          AS src_id,
               type(last_r)         AS rel_type,
               dst_node.id          AS dst_id
        LIMIT 300
        """
        try:
            return self._run(query, id=entity_id)
        except Exception as exc:
            logger.error("get_neighbors 실패 (id=%s): %s", entity_id, exc)
            return []

    def get_chunks_for_nodes(self, node_ids: list[str]) -> list[dict]:
        """구조 노드 ID 목록에 FOUND_IN으로 연결된 Chunk 반환."""
        if not node_ids:
            return []
        rows = self._run(
            """
            MATCH (n)-[:FOUND_IN]->(c:Chunk)
            WHERE n.id IN $ids
            RETURN DISTINCT
                c.id          AS id,
                c.text        AS text,
                c.source_file AS source_file,
                c.source_page AS source_page,
                c.doc_version AS doc_version
            """,
            ids=node_ids,
        )
        return rows

    def entity_exists(self, entity_id: str) -> bool:
        rows = self._run("MATCH (n:Entity {id: $id}) RETURN n.id", id=entity_id)
        return bool(rows)

    def flag_needs_review_by_source(self, source_file: str) -> int:
        """특정 소스 파일 기반 Chunk·Entity에 needs_review=true 플래그."""
        self._run_write(
            "MATCH (c:Chunk {source_file: $sf}) SET c.needs_review = true", sf=source_file
        )
        self._run_write(
            "MATCH (e:Entity {source: $sf}) SET e.needs_review = true", sf=source_file
        )
        return 1

    # ─── review_queue 관리 ───────────────────────────────────────────────────
    def _add_to_review_queue(self, triple: Triple) -> None:
        queue = self._load_review_queue()
        queue.append({
            "subject_id": triple.subject_id,
            "predicate": triple.predicate,
            "object_id": triple.object_id,
            "confidence": triple.confidence,
            "source": triple.source,
            "created_at": _now(),
        })
        REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)

    def _load_review_queue(self) -> list[dict]:
        if REVIEW_QUEUE_PATH.exists():
            with open(REVIEW_QUEUE_PATH, encoding="utf-8") as f:
                return json.load(f)
        return []

    # ─── 연결 관리 ───────────────────────────────────────────────────────────
    def verify_connectivity(self) -> bool:
        """Neo4j 연결 상태를 확인한다."""
        try:
            self._driver.verify_connectivity()
            return True
        except ServiceUnavailable as exc:
            logger.error("Neo4j 연결 실패: %s", exc)
            return False

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "GraphStore":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ─── 유틸 ────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now().isoformat()
