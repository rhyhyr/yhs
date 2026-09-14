# -*- coding: utf-8 -*-
"""
experiments/threshold_sweep.py

_MIN_CHUNK_SCORE × GATE_MIN_TOP_SCORE 격자 스윕.
한국어 in_db + complex 질문(정적 정답 있음)만 사용.

python experiments/threshold_sweep.py
"""
from __future__ import annotations

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("RUNTIME_LLM", "ollama")
from dotenv import load_dotenv
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=True)

import agent.retrieval_engine as re_module
from agent.agent_runtime import GateThresholds, should_use_deep_path
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

from 실험.YHS_eval_questions_100 import EVAL_QUERIES

# 한국어 in_db + complex (정적 정답이 있는 항목만)
TARGET_QUERIES = [
    q for q in EVAL_QUERIES
    if q["lang"] == "ko" and q["stratum"] in ("in_db", "complex")
]
print(f"스윕 대상: {len(TARGET_QUERIES)}개 (ko in_db+complex)")

# 스윕 격자
MIN_CHUNK_SCORES = [0.20, 0.25, 0.28, 0.30, 0.33, 0.35, 0.38, 0.40]
GATE_SCORES      = [0.20, 0.25, 0.30, 0.35]


def run_sweep(store, embedder):
    from agent.retrieval_engine import RetrievalEngine

    results = []

    for mcs in MIN_CHUNK_SCORES:
        # 모듈 변수 패치
        re_module._MIN_CHUNK_SCORE = mcs

        for gate in GATE_SCORES:
            thresholds = GateThresholds(min_top_score=gate, min_evidence_chunks=2)
            engine = RetrievalEngine(store, embedder)

            no_answer_cnt = 0
            deep_cnt = 0
            total_chunks = 0
            total_best = 0.0
            n = 0

            for q in TARGET_QUERIES:
                try:
                    result = engine.retrieve(q["query"])
                    best = max((c.score for c in result.chunks), default=0.0)
                    chunks = len(result.chunks)
                    no_ans = result.retrieval_method == "no_answer"
                    use_deep, _ = should_use_deep_path(q["query"], best, chunks, thresholds)

                    no_answer_cnt += int(no_ans)
                    deep_cnt += int(use_deep)
                    if not no_ans:
                        total_chunks += chunks
                        total_best += best
                    n += 1
                except Exception:
                    n += 1
                    no_answer_cnt += 1

            answered = n - no_answer_cnt
            avg_chunks = total_chunks / answered if answered else 0
            avg_best   = total_best / answered if answered else 0
            recall     = answered / n  # 답 시도율 (proxy)

            results.append({
                "min_chunk": mcs,
                "gate": gate,
                "recall": round(recall, 3),
                "no_ans": no_answer_cnt,
                "deep_pct": round(deep_cnt / n, 3),
                "avg_chunks": round(avg_chunks, 2),
                "avg_best": round(avg_best, 3),
            })

            print(
                f"  mcs={mcs:.2f} gate={gate:.2f} | "
                f"recall={recall:.1%} no_ans={no_answer_cnt:2d}/{n} "
                f"deep={deep_cnt/n:.0%} "
                f"avg_chunks={avg_chunks:.1f} avg_best={avg_best:.3f}"
            )

    return results


def print_table(results):
    print("\n" + "=" * 90)
    print("_MIN_CHUNK_SCORE x GATE 격자 스윕 결과 (한국어 in_db+complex)")
    print(f"{'min_chunk':>10} {'gate':>6} | {'recall':>7} {'no_ans':>7} {'deep%':>6} {'avg_chunks':>10} {'avg_best':>9}")
    print("-" * 90)

    best_row = max(results, key=lambda r: (r["recall"], r["avg_best"], -r["avg_chunks"]))

    for r in results:
        marker = " ◀ best" if r == best_row else ""
        print(
            f"{r['min_chunk']:>10.2f} {r['gate']:>6.2f} | "
            f"{r['recall']:>7.1%} {r['no_ans']:>7} {r['deep_pct']:>6.0%} "
            f"{r['avg_chunks']:>10.1f} {r['avg_best']:>9.3f}{marker}"
        )

    print("=" * 90)
    print(f"\n권장: _MIN_CHUNK_SCORE={best_row['min_chunk']}, GATE_MIN_TOP_SCORE={best_row['gate']}")
    print(f"  → recall={best_row['recall']:.1%}, avg_best={best_row['avg_best']:.3f}, avg_chunks={best_row['avg_chunks']:.1f}")


def main():
    print("Embedder 로딩 중...")
    embedder = Embedder()
    with GraphStore() as store:
        print("스윕 시작...\n")
        results = run_sweep(store, embedder)
    print_table(results)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    main()
