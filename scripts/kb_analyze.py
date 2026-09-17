"""
scripts/kb_analyze.py

kb_extract.py 가 저장한 raw JSONL 에 파싱·검증을 다시 적용하고 전수 분석한다.
API 를 호출하지 않으므로 검증 규칙을 고쳐 가며 몇 번이든 돌릴 수 있다.

내는 것:
    1) 중간 파일 (JSONL)  청크별 chunk_type, 채택/폐기 엔티티·관계와 그 사유
    2) 표준출력 분석      chunk_type 분포, Entity type, predicate, endpoint 누락,
                          type×predicate 오류, 폐기 사유, 문서별 이상치

실행:
    docker compose exec -T -e PYTHONIOENCODING=utf-8 backend \
        python - < scripts/kb_analyze.py

    환경변수
      RAW   입력 JSONL (기본 /data/extract/raw.jsonl)
      OUT   중간 파일  (기본 /data/extract/validated.jsonl)
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from yhs.ingest.pipeline.extractor import LLMExtractor
from yhs.ingest.stats import STATS
from yhs.ingest.validation import (
    DESCRIPTIVE_CHUNK_TYPES,
    normalize_chunk_type,
)
from yhs.schema.types import ChunkNode

RAW = Path(os.getenv("RAW", "/data/extract/raw.jsonl"))
OUT = Path(os.getenv("OUT", "/data/extract/validated.jsonl"))

BAR = "─" * 62


def h(title: str) -> None:
    print(f"\n{BAR}\n  {title}\n{BAR}")


def table(counter: Counter, total: int | None = None, indent: str = "    ") -> None:
    if not counter:
        print(f"{indent}(없음)")
        return
    total = total or sum(counter.values())
    width = max(len(str(k)) for k in counter)
    for k, v in counter.most_common():
        pct = v / total * 100 if total else 0
        print(f"{indent}{str(k):{width}}  {v:5}  {pct:5.1f}%  {'█' * int(pct / 2)}")


def main() -> int:
    if not RAW.is_file():
        print(f"입력이 없습니다: {RAW}")
        return 1

    records = [json.loads(l) for l in RAW.open(encoding="utf-8") if l.strip()]
    print(f"입력 {RAW}  —  {len(records)}청크")
    meta = records[0]
    print(f"model={meta['model']}  prompt_version={meta['prompt_version']}  "
          f"schema={meta['schema_hash']}")

    errored = [r for r in records if r.get("error")]
    if errored:
        print(f"\n  [주의] 추출 실패 {len(errored)}청크 — 분석에서 제외됩니다")
        for r in errored[:5]:
            print(f"      {r['source_file'][:40]}  {r['error'][:70]}")

    STATS.reset()
    extractor = LLMExtractor()

    # ── 집계 통 ─────────────────────────────────────────────────────────
    chunk_types = Counter()
    raw_chunk_types = Counter()
    entity_types = Counter()
    pred_kept = Counter()
    pred_dropped = Counter()
    drop_reasons = Counter()
    orphan_names = Counter()
    mismatch_combo = Counter()
    mismatch_examples: dict[str, list[str]] = defaultdict(list)
    entity_block_reasons = Counter()
    per_doc: dict[str, dict] = defaultdict(
        lambda: {"chunks": 0, "ent_kept": 0, "rel_parsed": 0, "rel_kept": 0,
                 "types": Counter(), "reasons": Counter()})

    out_lines = []

    for rec in records:
        if rec.get("error"):
            continue
        raw = rec["raw_response"] or {}
        doc = rec["source_file"]
        raw_ct = (raw.get("chunk_type") or "").strip().lower()
        ctype, unknown = normalize_chunk_type(raw_ct)
        raw_chunk_types[raw_ct or "(비어 있음)"] += 1
        chunk_types[ctype] += 1

        chunk = ChunkNode(id=rec["chunk_id"], text=rec["chunk_text"],
                          source_file=doc, source_page=rec["source_page"])

        # 실제 적재와 같은 경로를 탄다 — 분석용 로직을 따로 짜지 않는다.
        entities = extractor._parse_entities(raw.get("entities", []) or [], chunk)
        triples = extractor._parse_triples(raw.get("relations", []) or [], chunk)
        n_parsed_rel = len(triples)

        trace: list[dict] = []
        from yhs.ingest.validation import validate
        kept_ents, kept_rels = validate(entities, triples, raw_ct, trace=trace)

        d = per_doc[doc]
        d["chunks"] += 1
        d["ent_kept"] += len(kept_ents)
        d["rel_parsed"] += n_parsed_rel
        d["rel_kept"] += len(kept_rels)
        d["types"][ctype] += 1

        for e in kept_ents:
            entity_types[e.type or "(타입 없음)"] += 1

        for t in trace:
            if t["kind"] == "entity":
                if t["verdict"] == "dropped":
                    entity_block_reasons[t["reason"]] += 1
                continue
            if t["verdict"] == "kept":
                pred_kept[t["predicate"]] += 1
            else:
                pred_dropped[t["predicate"]] += 1
                drop_reasons[t["reason"]] += 1
                d["reasons"][t["reason"]] += 1
                if t["reason"] == "endpoint 누락":
                    orphan_names.update(t.get("missing") or [])
                elif t["reason"] == "타입 불일치":
                    combo = (f"{t.get('subject_type')} -[{t['predicate']}]-> "
                             f"{t.get('object_type')}")
                    mismatch_combo[combo] += 1
                    if len(mismatch_examples[combo]) < 3:
                        mismatch_examples[combo].append(
                            f"{t['subject']} -[{t['predicate']}]-> {t['object']}")

        out_lines.append(json.dumps({
            "chunk_id": rec["chunk_id"],
            "source_file": doc,
            "source_page": rec["source_page"],
            "chunk_sha1": rec["chunk_sha1"],
            "model": rec["model"],
            "prompt_version": rec["prompt_version"],
            "schema_hash": rec["schema_hash"],
            "chunk_type_raw": raw_ct,
            "chunk_type": ctype,
            "chunk_type_unknown": unknown,
            "entities": [{"id": e.id, "name": e.name, "type": e.type,
                          "summary": e.summary, "confidence": e.confidence}
                         for e in kept_ents],
            "relations": [{"subject": t.subject_id, "predicate": t.predicate,
                           "object": t.object_id, "evidence": t.evidence,
                           "condition": t.condition, "confidence": t.confidence}
                          for t in kept_rels],
            "trace": trace,
        }, ensure_ascii=False))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    n_chunks = sum(chunk_types.values())
    rel_parsed = sum(pred_kept.values()) + sum(pred_dropped.values())
    rel_kept = sum(pred_kept.values())

    # ── 1. chunk_type 분포 ──────────────────────────────────────────────
    h("1. chunk_type 분포")
    table(chunk_types, n_chunks)
    off = {k: v for k, v in raw_chunk_types.items()
           if k not in chunk_types and k != "(비어 있음)"}
    if off:
        print(f"\n    목록 밖 값 → descriptive 처리: {off}")
    desc_n = sum(v for k, v in chunk_types.items() if k in DESCRIPTIVE_CHUNK_TYPES)
    print(f"\n    설명성 문단(관계 차단 대상) {desc_n}/{n_chunks} "
          f"= {desc_n / n_chunks * 100:.0f}%")

    # ── 2. Entity type ──────────────────────────────────────────────────
    h("2. Entity type 분포 (채택된 것)")
    table(entity_types)
    print("\n    엔티티 차단 사유")
    table(entity_block_reasons, indent="      ")

    # ── 3. predicate ────────────────────────────────────────────────────
    h("3. predicate 채택 / 폐기")
    print(f"    파싱 {rel_parsed}건 → 채택 {rel_kept}건 "
          f"({rel_kept / max(rel_parsed, 1) * 100:.0f}%) / "
          f"폐기 {rel_parsed - rel_kept}건\n")
    width = max([len(p) for p in set(pred_kept) | set(pred_dropped)] or [10])
    print(f"    {'predicate':{width}}  {'채택':>6} {'폐기':>6}  채택률")
    for p in sorted(set(pred_kept) | set(pred_dropped),
                    key=lambda x: -(pred_kept[x] + pred_dropped[x])):
        k, dr = pred_kept[p], pred_dropped[p]
        print(f"    {p:{width}}  {k:6} {dr:6}  {k / max(k + dr, 1) * 100:5.0f}%")

    # ── 4. 폐기 사유 ────────────────────────────────────────────────────
    h("4. 관계 폐기 사유")
    table(drop_reasons, rel_parsed - rel_kept)

    # ── 5. endpoint 누락 ────────────────────────────────────────────────
    h("5. endpoint 누락 — entities 에 없는 이름")
    print(f"    총 {drop_reasons['endpoint 누락']}건, 고유 이름 {len(orphan_names)}개\n")
    for n, cnt in orphan_names.most_common(20):
        mark = "  ← 30자 초과(엔티티 차단 대상)" if len(n) > 30 else ""
        print(f"      {cnt:3}회  {n[:60]}{mark}")

    # ── 6. type×predicate 오류 ──────────────────────────────────────────
    h("6. type × predicate 오류")
    print(f"    총 {drop_reasons['타입 불일치']}건, 조합 {len(mismatch_combo)}종\n")
    for combo, cnt in mismatch_combo.most_common(15):
        print(f"      {cnt:3}회  {combo}")
        for ex in mismatch_examples[combo][:2]:
            print(f"             예) {ex}")

    # ── 7. 문서별 이상치 ────────────────────────────────────────────────
    h("7. 문서별 — 관계 채택률이 낮거나 관계가 0인 문서")
    rows = []
    for doc, d in per_doc.items():
        rate = d["rel_kept"] / d["rel_parsed"] * 100 if d["rel_parsed"] else -1
        rows.append((rate, doc, d))
    rows.sort(key=lambda r: (r[0]))
    print(f"    {'문서':44} {'청크':>4} {'엔티티':>6} {'관계':>11} {'채택률':>7}  주 폐기사유")
    for rate, doc, d in rows:
        rate_s = "  파싱0" if rate < 0 else f"{rate:5.0f}%"
        top = d["reasons"].most_common(1)
        top_s = f"{top[0][0]}({top[0][1]})" if top else ""
        flag = " ⚠" if (rate >= 0 and rate < 50) or d["rel_kept"] == 0 else "  "
        print(f"  {flag}{doc[:42]:44} {d['chunks']:4} {d['ent_kept']:6} "
              f"{d['rel_kept']:4}/{d['rel_parsed']:<6} {rate_s}  {top_s}")

    # ── 8. 요약 ─────────────────────────────────────────────────────────
    h("8. 적재하면 이렇게 됩니다")
    print(f"    청크        {n_chunks}")
    print(f"    엔티티      {sum(entity_types.values())} (중복 병합 전)")
    print(f"    관계        {rel_kept}")
    print(f"    관계 채택률 {rel_kept / max(rel_parsed, 1) * 100:.0f}%")
    print(f"\n    중간 파일: {OUT}")
    print("    규칙을 고쳤다면 이 스크립트만 다시 돌리면 됩니다 (API 호출 없음).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
