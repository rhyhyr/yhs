"""
scripts/copy_graph.py

Neo4j 인스턴스 사이로 그래프를 그대로 옮긴다.

쓰는 상황:
    호스트의 Neo4j Desktop 에 만들어 둔 지식베이스를 도커 컨테이너의
    Neo4j 로 옮겨, `docker compose up` 만으로 동작하는 자립형 스택을 만들 때.
    재인제스트와 달리 LLM 을 부르지 않으므로 API 비용이 0 이다.

모든 쓰기는 id 기준 MERGE 라 여러 번 돌려도 안전하다(멱등).

설정은 환경변수로 받는다 — 비밀번호가 명령행(ps 출력)에 남지 않도록:

    SRC_URI, SRC_USER, SRC_PASSWORD
    DST_URI, DST_USER, DST_PASSWORD

실행 (백엔드 컨테이너 안에서 — 양쪽에 모두 닿을 수 있는 유일한 위치):

    docker compose exec -T \
      -e SRC_URI=neo4j://host.docker.internal:7687 -e SRC_PASSWORD=... \
      -e DST_URI=neo4j://neo4j:7687              -e DST_PASSWORD=... \
      backend python - < scripts/copy_graph.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

from neo4j import GraphDatabase

# 한 번에 옮길 노드/관계 수. Chunk 는 1024차원 임베딩을 들고 있어
# 너무 크게 잡으면 트랜잭션이 무거워진다.
BATCH = 100


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        sys.exit(f"환경변수 {name} 가 필요합니다.")
    return value


def fetch_labels(session: Any) -> list[str]:
    return [r["label"] for r in session.run(
        "MATCH (n) UNWIND labels(n) AS label "
        "RETURN DISTINCT label ORDER BY label"
    )]


def ensure_constraints(session: Any, labels: list[str]) -> None:
    """대상에 id 유니크 제약을 만든다. MERGE 성능과 정합성 양쪽에 필요하다."""
    for label in labels:
        session.run(
            f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
            f"FOR (n:`{label}`) REQUIRE n.id IS UNIQUE"
        )
    print(f"  제약조건 확인/생성: {', '.join(labels)}")


def copy_nodes(src: Any, dst: Any, label: str) -> int:
    total = src.run(f"MATCH (n:`{label}`) RETURN count(n) AS c").single()["c"]
    moved = 0
    while moved < total:
        rows = [r["props"] for r in src.run(
            f"MATCH (n:`{label}`) RETURN properties(n) AS props "
            f"ORDER BY n.id SKIP $skip LIMIT $limit",
            skip=moved, limit=BATCH,
        )]
        if not rows:
            break
        dst.run(
            f"UNWIND $rows AS props "
            f"MERGE (n:`{label}` {{id: props.id}}) SET n = props",
            rows=rows,
        )
        moved += len(rows)
        print(f"    {label}: {moved}/{total}", end="\r", flush=True)
    print(f"    {label}: {moved}/{total}   ")
    return moved


def copy_relationships(src: Any, dst: Any) -> int:
    total = src.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    moved = 0
    while moved < total:
        rows = [
            {
                "start": r["start"],
                "end": r["end"],
                "type": r["type"],
                "props": r["props"],
            }
            for r in src.run(
                "MATCH (a)-[r]->(b) "
                "RETURN a.id AS start, b.id AS end, type(r) AS type, "
                "       properties(r) AS props "
                "ORDER BY a.id, type(r), b.id SKIP $skip LIMIT $limit",
                skip=moved, limit=BATCH,
            )
        ]
        if not rows:
            break

        # 관계 타입은 파라미터로 못 넘기므로 타입별로 묶어서 실행한다.
        by_type: dict[str, list[dict]] = {}
        for row in rows:
            by_type.setdefault(row["type"], []).append(row)

        for rel_type, group in by_type.items():
            dst.run(
                f"UNWIND $rows AS row "
                f"MATCH (a {{id: row.start}}), (b {{id: row.end}}) "
                f"MERGE (a)-[r:`{rel_type}`]->(b) SET r = row.props",
                rows=group,
            )
        moved += len(rows)
        print(f"    관계: {moved}/{total}", end="\r", flush=True)
    print(f"    관계: {moved}/{total}   ")
    return moved


def summarize(session: Any, title: str) -> None:
    nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    chunks = session.run("MATCH (c:Chunk) RETURN count(c) AS c").single()["c"]
    embedded = session.run(
        "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS c"
    ).single()["c"]
    print(f"  {title}: 노드 {nodes}, 관계 {rels}, Chunk {chunks} (임베딩 {embedded})")


def main() -> None:
    src_driver = GraphDatabase.driver(
        _env("SRC_URI"), auth=(_env("SRC_USER", "neo4j"), _env("SRC_PASSWORD"))
    )
    dst_driver = GraphDatabase.driver(
        _env("DST_URI"), auth=(_env("DST_USER", "neo4j"), _env("DST_PASSWORD"))
    )

    with src_driver.session() as src, dst_driver.session() as dst:
        print("이관 전 상태")
        summarize(src, "원본 ")
        summarize(dst, "대상 ")

        labels = fetch_labels(src)
        print(f"\n라벨: {labels}")
        ensure_constraints(dst, labels)

        print("\n노드 복사")
        for label in labels:
            copy_nodes(src, dst, label)

        print("\n관계 복사")
        copy_relationships(src, dst)

        print("\n이관 후 상태")
        summarize(src, "원본 ")
        summarize(dst, "대상 ")

        # 검증 — 노드/관계 수가 맞는지 확인한다.
        src_n = src.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        dst_n = dst.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        src_r = src.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        dst_r = dst.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

        if (src_n, src_r) == (dst_n, dst_r):
            print("\n검증 통과 — 노드·관계 수가 일치합니다.")
        else:
            print(f"\n[경고] 수가 다릅니다: 노드 {src_n}→{dst_n}, 관계 {src_r}→{dst_r}")
            sys.exit(1)

    src_driver.close()
    dst_driver.close()


if __name__ == "__main__":
    main()
