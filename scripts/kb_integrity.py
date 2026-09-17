"""
scripts/kb_integrity.py

인제스트 직후 지식베이스의 무결성을 검사한다.

확인 항목:
  1. source document 수            — data/sources 와 KB 가 일치하는가
  2. chunk 수 / chunk id 중복
  3. min/max 토큰 위반 / 빈 chunk
  4. 존재하지 않는 chunk 를 가리키는 FOUND_IN
  5. 존재하지 않는 entity 를 가리키는 relation
  6. orphan chunk (엔티티 연결 없음)
  7. 의미 관계가 없는 entity

실행 (컨테이너 안):
    docker compose exec -T backend python - < scripts/kb_integrity.py
"""

from __future__ import annotations

import pathlib
import sys

from yhs.core.config import MAX_CHUNK_TOKENS, MIN_CHUNK_TOKENS, PDF_DIR
from yhs.infra.graph_store import GraphStore

FAIL = []
WARN = []


def check(label: str, ok: bool, detail: str = "", warn_only: bool = False) -> None:
    mark = "OK  " if ok else ("WARN" if warn_only else "FAIL")
    print(f"  [{mark}] {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        (WARN if warn_only else FAIL).append(f"{label}: {detail}")


def main() -> None:
    from yhs.ingest.pipeline.chunker import _token_count

    src_files = sorted(p.name for p in pathlib.Path(PDF_DIR).glob("*.pdf"))

    with GraphStore() as store, store._driver.session() as s:
        print("\n── 1. 문서 ───────────────────────────────────────────────")
        kb_files = {r["f"] for r in s.run(
            "MATCH (c:Chunk) RETURN DISTINCT c.source_file AS f") if r["f"]}
        missing = [f for f in src_files if f not in kb_files]
        extra = [f for f in kb_files if f not in src_files]
        check(f"source document 수 (원본 {len(src_files)} / KB {len(kb_files)})",
              not missing and not extra,
              f"누락 {missing} / 잉여 {extra}" if (missing or extra) else "")

        print("\n── 2. 청크 ───────────────────────────────────────────────")
        total = s.run("MATCH (c:Chunk) RETURN count(c) AS n").single()["n"]
        distinct_id = s.run("MATCH (c:Chunk) RETURN count(DISTINCT c.id) AS n").single()["n"]
        distinct_text = s.run("MATCH (c:Chunk) RETURN count(DISTINCT c.text) AS n").single()["n"]
        print(f"         chunk 수 {total}, 고유 id {distinct_id}, 고유 본문 {distinct_text}")
        check("chunk id 중복 없음", total == distinct_id, f"{total - distinct_id}건 중복")
        check("동일 본문 중복 없음", total == distinct_text,
              f"{total - distinct_text}건 중복", warn_only=True)

        print("\n── 3. 청크 품질 ──────────────────────────────────────────")
        empty = s.run(
            "MATCH (c:Chunk) WHERE c.text IS NULL OR trim(c.text) = '' "
            "RETURN count(c) AS n").single()["n"]
        check("빈 chunk 없음", empty == 0, f"{empty}건")

        no_emb = s.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NULL RETURN count(c) AS n").single()["n"]
        check("임베딩 누락 없음", no_emb == 0, f"{no_emb}건")

        texts = [r["t"] for r in s.run("MATCH (c:Chunk) RETURN c.text AS t") if r["t"]]
        toks = [_token_count(t) for t in texts]
        under = sum(1 for t in toks if t < MIN_CHUNK_TOKENS)
        over = sum(1 for t in toks if t > MAX_CHUNK_TOKENS)
        if toks:
            toks_sorted = sorted(toks)
            med = toks_sorted[len(toks_sorted) // 2]
            print(f"         토큰 min={min(toks)} median={med} max={max(toks)}")
        check(f"MIN({MIN_CHUNK_TOKENS}) 미만 없음", under == 0, f"{under}건", warn_only=True)
        check(f"MAX({MAX_CHUNK_TOKENS}) 초과 없음", over == 0, f"{over}건", warn_only=True)

        print("\n── 4. 참조 무결성 ────────────────────────────────────────")
        # FOUND_IN 은 Entity → Chunk 로만 가야 한다.
        bad_found_in = s.run(
            "MATCH ()-[r:FOUND_IN]->(x) WHERE NOT x:Chunk RETURN count(r) AS n"
        ).single()["n"]
        check("FOUND_IN 대상이 모두 Chunk", bad_found_in == 0, f"{bad_found_in}건")

        dangling_rel = s.run(
            "MATCH (a)-[r]->(b) WHERE type(r) <> 'FOUND_IN' "
            "AND (a.id IS NULL OR b.id IS NULL) RETURN count(r) AS n"
        ).single()["n"]
        check("관계 양끝에 id 존재", dangling_rel == 0, f"{dangling_rel}건")

        # 라벨이 없는(= 관계 때문에 암묵 생성된) 노드
        untyped = s.run(
            "MATCH (n) WHERE size(labels(n)) = 0 RETURN count(n) AS n").single()["n"]
        check("라벨 없는 노드 없음", untyped == 0, f"{untyped}건 — 존재하지 않는 엔티티를 "
                                                  f"가리키는 관계가 만든 빈 노드")

        print("\n── 5. 연결성 ─────────────────────────────────────────────")
        orphan_chunk = s.run(
            "MATCH (c:Chunk) WHERE NOT (:Entity)-[:FOUND_IN]->(c) RETURN count(c) AS n"
        ).single()["n"]
        check(f"orphan chunk ({orphan_chunk}/{total})", orphan_chunk == 0,
              f"{orphan_chunk}건 — 그래프로는 닿을 수 없음", warn_only=True)

        ent_total = s.run("MATCH (e:Entity) RETURN count(e) AS n").single()["n"]
        no_sem = s.run(
            "MATCH (e:Entity) WHERE NOT (e)-[]-() OR NOT EXISTS { "
            "  MATCH (e)-[r]-() WHERE type(r) <> 'FOUND_IN' } "
            "RETURN count(e) AS n"
        ).single()["n"]
        check(f"의미 관계 없는 entity ({no_sem}/{ent_total})", no_sem == 0,
              f"{no_sem}건 — 사실상 키워드 태그", warn_only=True)

    print("\n" + "=" * 62)
    if FAIL:
        print(f"  FAIL {len(FAIL)}건")
        for f in FAIL:
            print("    -", f)
    else:
        print("  치명적 결함 없음")
    if WARN:
        print(f"  WARN {len(WARN)}건 (구조 개선 대상)")
        for w in WARN:
            print("    -", w)
    print("=" * 62 + "\n")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
