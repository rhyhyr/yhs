"""
scripts/kb_reset.py

지식베이스를 비운다 (clean rebuild 용).

지우는 것:
    Chunk, Entity, Procedure, Document, Institution, Domain, Topic 및 이들에
    붙은 모든 관계. ExternalChunk / ExternalSource(웹 크롤 캐시)도 함께.

남기는 것:
    유니크 제약과 벡터 인덱스. 스키마까지 지우면 재인제스트 때 다시 만들어야
    하고, MERGE 성능도 떨어진다.

실행 전에 현재 상태를 출력하고, CONFIRM=yes 가 있어야 실제로 지운다.

    docker compose exec -T -e CONFIRM=yes backend python - < scripts/kb_reset.py
"""

from __future__ import annotations

import os
import sys

from yhs.infra.graph_store import GraphStore

# 지울 노드 라벨. ExternalChunk/ExternalSource 는 웹 크롤 캐시라 같이 비운다.
_LABELS = [
    "Chunk", "Entity", "Procedure", "Document", "Institution", "Domain", "Topic",
    "ExternalChunk", "ExternalSource",
]


def snapshot(session) -> dict[str, int]:
    rows = session.run(
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC"
    )
    counts = {r["label"] or "(라벨없음)": r["cnt"] for r in rows}
    rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
    counts["__관계__"] = rels
    return counts


def main() -> None:
    with GraphStore() as store, store._driver.session() as s:
        before = snapshot(s)
        print("\n초기화 전:")
        for k, v in before.items():
            print(f"  {k:20} {v:>6}")

        if os.environ.get("CONFIRM", "").lower() != "yes":
            print("\nCONFIRM=yes 가 없어 아무것도 지우지 않았습니다.")
            sys.exit(0)

        print("\n삭제 중...")
        for label in _LABELS:
            # 관계까지 함께 지우려면 DETACH DELETE.
            # 한 번에 다 지우면 트랜잭션이 커지므로 배치로 끊는다.
            while True:
                n = s.run(
                    f"MATCH (n:`{label}`) WITH n LIMIT 500 DETACH DELETE n "
                    f"RETURN count(n) AS n"
                ).single()["n"]
                if not n:
                    break
            print(f"  {label} 삭제 완료")

        # 관계만 남아 생긴 라벨 없는 노드 정리
        while True:
            n = s.run(
                "MATCH (n) WHERE size(labels(n)) = 0 WITH n LIMIT 500 "
                "DETACH DELETE n RETURN count(n) AS n"
            ).single()["n"]
            if not n:
                break

        after = snapshot(s)
        print("\n초기화 후:")
        for k, v in after.items():
            print(f"  {k:20} {v:>6}")

        leftover = sum(v for k, v in after.items() if k != "__관계__")
        if leftover or after.get("__관계__"):
            print(f"\n[경고] 남은 노드/관계가 있습니다: {after}")
            sys.exit(1)
        print("\n지식베이스를 비웠습니다 (제약·인덱스는 유지).")


if __name__ == "__main__":
    main()
