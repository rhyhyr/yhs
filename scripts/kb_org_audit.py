"""
scripts/kb_org_audit.py

ORGANIZATION 노드가 그래프에 꼭 있어야 하는지 raw 추출 결과로 따진다.

배경:
    147청크 전수에서 채택 엔티티의 54.5%(1,288/2,362)가 ORGANIZATION 이었다.
    대부분 기관 소개·오시는 길·소속기관 목록 문서에서 나오는데, 그 문단들은
    설명성으로 분류돼 관계가 거의 만들어지지 않는다. 즉 노드만 늘고 엣지는
    없다. 엔티티에서 1~2홉 확장하는 검색에서 이런 노드는 확장 경로를
    만들지 못하고 그래프만 무겁게 한다.

    다만 이름 자체는 검색에 쓸모가 있다 — "부산출입국외국인청" 을 물으면
    그 이름이 들어간 청크를 찾아야 한다. 그건 Chunk 본문과 임베딩이 이미
    하고 있는 일이다. 그래프 노드로 또 둘 필요가 있는지가 질문이다.

내는 것:
    문단 유형별 ORGANIZATION 생성량, 채택 관계 참여 여부, 문서별 집중도,
    그리고 "관계에 한 번도 안 쓰인 기관" 이 실제로 어떤 것들인지.

실행:
    docker compose exec -T -e PYTHONIOENCODING=utf-8 backend \
        python - < scripts/kb_org_audit.py
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from yhs.ingest.pipeline.extractor import LLMExtractor
from yhs.ingest.stats import STATS
from yhs.ingest.validation import normalize_chunk_type, normalize_name, validate
from yhs.schema.types import ChunkNode

RAW = Path(os.getenv("RAW", "/data/extract/raw.jsonl"))
BAR = "─" * 62


def main() -> int:
    records = [json.loads(l) for l in RAW.open(encoding="utf-8") if l.strip()]
    STATS.reset()
    ex = LLMExtractor()

    # 기관 이름 → 나온 문단 유형 / 나온 문서 / 채택 관계 참여 횟수
    org_ctypes: dict[str, Counter] = defaultdict(Counter)
    org_docs: dict[str, set] = defaultdict(set)
    org_used: Counter = Counter()
    by_ctype_created = Counter()
    by_doc_created = Counter()
    other_types_created = 0

    for rec in records:
        if rec.get("error"):
            continue
        raw = rec["raw_response"] or {}
        ctype, _ = normalize_chunk_type(raw.get("chunk_type", ""))
        chunk = ChunkNode(id=rec["chunk_id"], text=rec["chunk_text"],
                          source_file=rec["source_file"],
                          source_page=rec["source_page"])
        ents = ex._parse_entities(raw.get("entities", []) or [], chunk)
        tris = ex._parse_triples(raw.get("relations", []) or [], chunk)
        kept_e, kept_r = validate(ents, tris, raw.get("chunk_type", ""))

        used = set()
        for t in kept_r:
            used.add(normalize_name(t.subject_id))
            used.add(normalize_name(t.object_id))

        for e in kept_e:
            if (e.type or "") != "ORGANIZATION":
                other_types_created += 1
                continue
            key = normalize_name(e.name)
            org_ctypes[key][ctype] += 1
            org_docs[key].add(rec["source_file"])
            by_ctype_created[ctype] += 1
            by_doc_created[rec["source_file"]] += 1
            if key in used:
                org_used[key] += 1

    total_org = len(org_ctypes)
    used_org = len(org_used)
    unused = total_org - used_org

    print(f"\n{BAR}\n  ORGANIZATION 감사 — raw 추출 {len(records)}청크 기준\n{BAR}")
    print(f"  고유 기관 이름            {total_org}개")
    print(f"  채택 관계에 참여          {used_org}개 ({used_org / max(total_org,1)*100:.0f}%)")
    print(f"  한 번도 참여 안 함        {unused}개 ({unused / max(total_org,1)*100:.0f}%)")
    print(f"  ORGANIZATION 외 엔티티    {other_types_created}건(중복 포함)")

    print(f"\n{BAR}\n  문단 유형별 ORGANIZATION 생성량 (중복 포함)\n{BAR}")
    tot = sum(by_ctype_created.values())
    for ct, n in by_ctype_created.most_common():
        print(f"    {ct:14} {n:5}  {n/tot*100:5.1f}%")

    # 설명성/목록 문단에서만 나오고 관계에 한 번도 안 쓰인 기관
    dead = []
    for key, cts in org_ctypes.items():
        if org_used.get(key):
            continue
        if all(c in {"descriptive", "location", "contact", "listing"} for c in cts):
            dead.append((key, sum(cts.values()), sorted(cts), sorted(org_docs[key])))

    print(f"\n{BAR}\n  설명성·목록 문단에서만 나오고 관계가 하나도 없는 기관\n{BAR}")
    print(f"    {len(dead)}개 / 전체 기관 {total_org}개 "
          f"= {len(dead)/max(total_org,1)*100:.0f}%")
    print("\n    예시 30개")
    for key, n, cts, docs in sorted(dead, key=lambda x: -x[1])[:30]:
        print(f"      {key[:40]:42} {n}회  {','.join(cts):24} {docs[0][:28]}")

    print(f"\n{BAR}\n  문서별 ORGANIZATION 생성량 상위\n{BAR}")
    for doc, n in by_doc_created.most_common(10):
        print(f"    {doc[:46]:48} {n:5}")

    print(f"\n{BAR}\n  이 기관들이 있는 청크는 벡터 검색으로 닿는가\n{BAR}")
    hit = sum(1 for key, _, _, _ in dead
              if any(key in normalize_name(r["chunk_text"]) for r in records))
    print(f"    {hit}/{len(dead)}개가 청크 본문에 그대로 들어 있음 "
          f"({hit/max(len(dead),1)*100:.0f}%)")
    print("    → 본문에 있으면 Chunk 임베딩·키워드 검색으로 닿는다.")
    print("      그래프 노드로 또 두어야 하는지는 '관계가 있는가' 로 갈린다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
