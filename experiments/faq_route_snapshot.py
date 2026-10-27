"""
FAQ fast path 라우팅 회귀 스냅샷 (오프라인, Neo4j/LLM/네트워크 불필요).

eval_questions_v2(80) + v3(100) 전 문항을 FastPathHandler 에 통과시켜
문항별 route 를 jsonl 로 남기고, 이전 스냅샷과 route 가 바뀐 문항만 diff 한다.

  route: "faq" | "rag_gate"(complex_indicators 차단) | "rag_nomatch"(미매칭·신뢰도 미달)

사용:
  python experiments/faq_route_snapshot.py --baseline experiments/results/faq_route_baseline.jsonl
  python experiments/faq_route_snapshot.py --compare  experiments/results/faq_route_baseline.jsonl
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))

from experiments.eval_sets.eval_questions_v2 import EVAL_QUERIES as V2  # noqa: E402
from experiments.eval_sets.eval_questions_v3 import EVAL_QUERIES as V3  # noqa: E402

# yhs.rag/__init__ 이 engine(neo4j 등)을 끌고 오므로 faq.py 만 파일 경로로 직접 로드한다.
_spec = importlib.util.spec_from_file_location(
    "yhs_faq_snapshot", os.path.join(_ROOT, "backend", "src", "yhs", "rag", "faq.py")
)
faq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(faq)


def _row(set_name: str, q: dict, handler) -> dict:
    query = q["query"]
    q_lower = query.lower().strip()
    gate = next((ind for ind in faq._COMPLEX_INDICATORS if ind in q_lower), None)
    answer, info = handler.match_with_score(query)
    if dataclasses.is_dataclass(info):
        info = dataclasses.asdict(info)

    if gate is not None:
        route, reason = "rag_gate", f"complex_indicator:{gate}"
    elif answer is None:
        route = "rag_nomatch"
        reason = info.get("reason") if isinstance(info, dict) else "keyword_miss"
    else:
        route, reason = "faq", None

    idx = next((i for i, (_, a) in enumerate(faq._FAQ_DB) if a == answer), None)
    if route != "faq" and isinstance(info, dict):
        idx = info.get("entry_index", idx)  # 신뢰도 미달로 막힌 경우 어느 엔트리였는지 보존

    return {
        "set": set_name, "id": q["id"], "stratum": q["stratum"], "query": query,
        "route": route, "matched_entry_index": idx, "score": info, "reason": reason,
    }


def snapshot() -> list[dict]:
    h = faq.FastPathHandler()
    return [_row(name, q, h) for name, qs in (("v2", V2), ("v3", V3)) for q in qs]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 콘솔에서 한글 깨짐 방지
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--baseline", metavar="OUT", help="현재 라우팅을 jsonl 로 저장")
    g.add_argument("--compare", metavar="FILE", help="저장된 스냅샷과 route 차이 출력")
    args = ap.parse_args()

    rows = snapshot()
    if args.baseline:
        os.makedirs(os.path.dirname(os.path.abspath(args.baseline)), exist_ok=True)
        with open(args.baseline, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"saved {len(rows)} rows → {args.baseline}")
        return

    with open(args.compare, encoding="utf-8") as f:
        before = {(r["set"], r["id"]): r for r in map(json.loads, f)}
    changed = [r for r in rows if before[(r["set"], r["id"])]["route"] != r["route"]]
    for r in changed:
        b = before[(r["set"], r["id"])]
        print(f"{r['set']}  {r['id']:<14} {r['stratum']:<10} {b['route']} → {r['route']}"
              f"  [{r['reason']}]  {r['query']}")
    print(f"\n{len(changed)} changed / {len(rows)} rows")
    for name in ("v2", "v3"):
        faq_hits = [r for r in rows if r["set"] == name and r["route"] == "faq"]
        bad = [r["id"] for r in faq_hits if r["stratum"] in ("cross_hop", "complex", "dirty")]
        print(f"{name}: faq={len(faq_hits)}  faq∩(cross_hop|complex|dirty)={len(bad)} {bad}")


if __name__ == "__main__":
    main()
