"""
scripts/kb_load.py

kb_analyze.py 가 만든 validated.jsonl 을 Neo4j 에 적재한다. LLM 을 부르지 않는다.

왜 따로 있나:
    기존 인제스트(yhs --ingest)는 PDF 로딩부터 LLM 추출까지 한 번에 한다.
    그러면 적재할 때마다 API 를 다시 부르게 되고, 무엇을 넣을지 미리 볼 수
    없다. 여기서는 이미 검증까지 끝난 결과만 읽어 그대로 넣는다. 적재 결과가
    kb_analyze.py 가 보여준 숫자와 정확히 같아야 한다.

    청크 본문은 raw.jsonl 에서 가져오고, 임베딩만 로컬 모델로 새로 만든다
    (bge-m3, API 아님).

주의:
    규칙 기반 추출기(RuleExtractor)는 타지 않는다. validated.jsonl 에 있는
    것만 넣는다 — 분석에서 보여준 숫자와 어긋나지 않게 하기 위해서다.

실행:
    docker compose exec -T -e PYTHONIOENCODING=utf-8 backend \
        python - < scripts/kb_load.py
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from yhs.infra.embedder import Embedder
from yhs.infra.graph_store import GraphStore
from yhs.ingest.pipeline.ingestor import GraphIngestor
from yhs.ingest.stats import STATS
from yhs.schema.types import ChunkNode, EntityNode, Triple

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW = Path(os.getenv("RAW", "/data/extract/raw.jsonl"))
VALIDATED = Path(os.getenv("VALIDATED", "/data/extract/validated.jsonl"))


def main() -> int:
    if not VALIDATED.is_file():
        print(f"검증 결과가 없습니다: {VALIDATED}")
        return 1

    raw_by_id = {}
    for line in RAW.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            raw_by_id[r["chunk_id"]] = r

    records = [json.loads(l) for l in VALIDATED.open(encoding="utf-8") if l.strip()]
    print(f"검증 결과 {len(records)}청크  (model={records[0]['model']}, "
          f"prompt_version={records[0]['prompt_version']})")

    STATS.reset()

    # ── 청크 ────────────────────────────────────────────────────────────
    chunks: list[ChunkNode] = []
    for rec in records:
        src = raw_by_id.get(rec["chunk_id"])
        if src is None:
            print(f"  [경고] raw 에 본문이 없어 건너뜀: {rec['chunk_id']}")
            continue
        chunks.append(ChunkNode(
            id=rec["chunk_id"],
            text=src["chunk_text"],
            source_file=rec["source_file"],
            source_page=rec["source_page"],
            section=src.get("section", ""),
        ))

    print(f"임베딩 생성 중… ({len(chunks)}청크, 로컬 bge-m3)")
    embedder = Embedder()
    for chunk, emb in zip(chunks, embedder.encode([c.text for c in chunks])):
        chunk.embedding = emb.tolist()

    # ── 엔티티 / 관계 / 연결 ────────────────────────────────────────────
    entities: list[EntityNode] = []
    triples: list[Triple] = []
    chunk_links: list[tuple[str, str]] = []

    for rec in records:
        for e in rec["entities"]:
            entities.append(EntityNode(
                id=e["id"], name=e["name"], domain="visa",
                type=e.get("type", ""), summary=e.get("summary", ""),
                confidence=float(e.get("confidence", 0.8)),
                source=rec["source_file"],
            ))
            chunk_links.append((e["id"], rec["chunk_id"]))
        for t in rec["relations"]:
            triples.append(Triple(
                subject_id=t["subject"], predicate=t["predicate"],
                object_id=t["object"], evidence=t.get("evidence", ""),
                condition=t.get("condition", ""),
                confidence=float(t.get("confidence", 0.8)),
                source=rec["source_file"], source_page=rec["source_page"],
            ))

    print(f"적재 대상  청크 {len(chunks)} / 엔티티 {len(entities)} "
          f"/ 관계 {len(triples)} / 연결 {len(chunk_links)}")

    with GraphStore() as store:
        GraphIngestor(store).ingest_all(chunks, entities, triples, chunk_links)

        rows = store._run("MATCH (n) RETURN labels(n)[0] AS label, "
                          "count(*) AS cnt ORDER BY cnt DESC")
        rels = store._run("MATCH ()-[r]->() RETURN type(r) AS rel, "
                          "count(*) AS cnt ORDER BY cnt DESC")

    print("\n" + "=" * 60)
    print("  적재 완료")
    for r in rows:
        print(f"    {r['label']:12} {r['cnt']}")
    print("  관계")
    for r in rels:
        print(f"    {r['rel']:20} {r['cnt']}")
    print("=" * 60)

    if STATS.relation_match_failed:
        print(f"\n  [주의] 엔티티가 없어 저장 못 한 관계 "
              f"{STATS.relation_match_failed}건")
        for s in STATS.match_failed_samples[:10]:
            print(f"      {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
