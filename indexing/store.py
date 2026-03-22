"""Neo4j 저장소 모듈.

역할:
- Neo4j 연결/인덱스 보장
- Document/Category/Chunk MERGE 저장
- 중복 확인 및 실행 요약 통계 조회
"""

from __future__ import annotations

import json
from contextlib import contextmanager

from neo4j import GraphDatabase

from .models import CategoryNode, Chunk


class Neo4jConnector:
    """인덱싱에 필요한 최소 Neo4j 읽기/쓰기 연산을 캡슐화한다."""
    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ping()

    def _ping(self) -> None:
        try:
            self._driver.verify_connectivity()
            print("✅ Neo4j 연결 성공!")
        except Exception as e:
            raise ConnectionError(
                f"\n[오류] Neo4j 연결 실패: {e}\n"
                "체크리스트:\n"
                "  1. Neo4j Desktop에서 DB Start 확인\n"
                "  2. .env의 NEO4J_PASSWORD 확인\n"
                "  3. 포트 확인: netstat -ano | findstr 7687\n"
            ) from e

    def close(self) -> None:
        self._driver.close()

    @contextmanager
    def session(self):
        with self._driver.session() as s:
            yield s

    def create_indexes(self) -> None:
        with self.session() as s:
            s.run("CREATE INDEX doc_key_idx IF NOT EXISTS FOR (d:Document) ON (d.doc_key)")
            s.run("CREATE INDEX category_id IF NOT EXISTS FOR (c:Category) ON (c.node_id)")
            s.run("CREATE INDEX chunk_id IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_id)")

    def is_indexed(self, doc_key: str) -> bool:
        with self.session() as s:
            rec = s.run(
                "MATCH (d:Document {doc_key: $k}) RETURN count(d) AS n",
                k=doc_key,
            ).single()
            return bool(rec and rec["n"] > 0)

    def save_document(self, doc_key: str, file_path: str) -> None:
        with self.session() as s:
            s.run(
                """
                MERGE (d:Document {doc_key: $doc_key})
                SET d.file_path = $file_path,
                    d.indexed_at = datetime()
                """,
                doc_key=doc_key,
                file_path=file_path,
            )

    def link_document_to_category(self, doc_key: str, node_id: str) -> None:
        with self.session() as s:
            s.run(
                """
                MERGE (d:Document {doc_key: $doc_key})
                ON CREATE SET d.indexed_at = datetime()
                MATCH (c:Category {node_id: $node_id})
                MERGE (d)-[:HAS_CATEGORY]->(c)
                """,
                doc_key=doc_key,
                node_id=node_id,
            )

    def merge_category(self, node: CategoryNode, doc_key: str) -> None:
        with self.session() as s:
            s.run(
                """
                MERGE (c:Category {node_id: $node_id})
                SET c.name = $name,
                    c.level = $level,
                    c.keywords_json = $kw,
                    c.embedding_json = $emb,
                    c.doc_key = $doc_key
                """,
                node_id=node.node_id,
                name=node.name,
                level=node.level,
                kw=json.dumps(node.keywords, ensure_ascii=False),
                emb=json.dumps(node.embedding.tolist() if node.embedding is not None else []),
                doc_key=doc_key,
            )

    def merge_subcategory_edge(self, parent_id: str, child_id: str) -> None:
        with self.session() as s:
            s.run(
                """
                MATCH (p:Category {node_id: $p})
                MATCH (c:Category {node_id: $c})
                MERGE (p)-[:HAS_SUBCATEGORY]->(c)
                """,
                p=parent_id,
                c=child_id,
            )

    def merge_chunk(self, chunk: Chunk, category_id: str, doc_key: str) -> None:
        with self.session() as s:
            s.run(
                """
                MERGE (ch:Chunk {chunk_id: $chunk_id})
                SET ch.text = $text,
                    ch.page = $page,
                    ch.embedding_json = $emb,
                    ch.doc_key = $doc_key
                WITH ch
                MATCH (cat:Category {node_id: $cat_id})
                MERGE (ch)-[:BELONGS_TO]->(cat)
                """,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                page=chunk.page,
                emb=json.dumps(chunk.embedding.tolist() if chunk.embedding is not None else []),
                doc_key=doc_key,
                cat_id=category_id,
            )

    def count_summary(self) -> dict[str, int]:
        with self.session() as s:
            return {
                "Document": s.run("MATCH (n:Document) RETURN count(n) AS c").single()["c"],
                "Category": s.run("MATCH (n:Category) RETURN count(n) AS c").single()["c"],
                "Chunk": s.run("MATCH (n:Chunk) RETURN count(n) AS c").single()["c"],
            }
