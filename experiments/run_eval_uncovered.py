"""
experiments/run_eval_uncovered.py
uncovered 20개만 크롤러 집중 실험

실행: python experiments/run_eval_uncovered.py
출력: experiments/results/runs_uncovered.jsonl
      experiments/results/scores_uncovered.jsonl
      experiments/results/results_uncovered.md
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("RUNTIME_LLM", "openai")

from dotenv import load_dotenv

load_dotenv()

from experiments.eval_sets.eval_questions_v3 import EVAL_QUERIES
from experiments.run_eval100 import aggregate, collect_answers, score_answers
from yhs.infra.embedder import Embedder
from yhs.infra.graph_store import GraphStore
from yhs.rag.llm.openai_client import OpenAIRuntimeClient
from yhs.rag.runtime import GateThresholds

RUNS_PATH   = "experiments/results/runs_uncovered.jsonl"
SCORES_PATH = "experiments/results/scores_uncovered.jsonl"
RESULTS_PATH = "experiments/results/results_uncovered.md"


def write_results_uncovered(runs: list[dict], scores: list[dict]) -> None:
    score_map = {s["id"]: s for s in scores}

    lines = [
        "# YHS 크롤러 실험 — uncovered 20개",
        "",
        f"> 측정일: {__import__('time').strftime('%Y-%m-%d')}",
        "> 크롤러 강제 호출 (needs_web=True)",
        "",
        "| id | query | snippets | answer[:80] | accuracy | grounded |",
        "|---|---|---|---|---|---|",
    ]

    pass_count = 0
    for r in runs:
        s = score_map.get(r["id"], {})
        acc = s.get("accuracy", "—")
        grounded = s.get("grounded", "—")
        sources = r.get("sources", [])
        snippet_count = sum(1 for src in sources if src == "")  # web 소스는 source_file이 없음
        has_web = "[WEB]" in r.get("answer", "")
        web_mark = "✅" if has_web else "❌"
        answer_preview = r.get("answer", "")[:80].replace("\n", " ")
        lines.append(
            f"| {r['id']} | {r['query'][:30]} | {web_mark} | {answer_preview} | {acc} | {grounded} |"
        )
        if has_web:
            pass_count += 1

    lines += [
        "",
        f"크롤러 응답 있음: {pass_count}/{len(runs)}",
    ]

    agg = aggregate(runs, scores)
    u = agg.get("uncovered", {})
    if u.get("quality_mean") is not None:
        lines += [
            "",
            f"답변 품질: {u['quality_mean']:.3f} / {u['quality_100']:.1f}점",
            f"근거 적합률: {u['grounded_rate']*100:.1f}%",
            f"환각률: {u['halluc_rate']*100:.1f}%",
            f"지연 p50/p95: {u['latency_p50']:.1f}s / {u['latency_p95']:.1f}s",
        ]

    md = "\n".join(lines)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print("\n" + "=" * 60)
    print(md)
    print("=" * 60)


def main() -> None:
    uncovered = [q for q in EVAL_QUERIES if q["stratum"] == "uncovered"]
    print(f"uncovered 질문: {len(uncovered)}개")
    for q in uncovered:
        print(f"  {q['id']}: {q['query'][:50]}")

    embedder = Embedder()
    thresholds = GateThresholds.from_config()
    llm = OpenAIRuntimeClient()
    if not llm.is_available():
        print("[FATAL] OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    with GraphStore() as store:
        runs = collect_answers(store, embedder, llm, thresholds, uncovered)

    with open(RUNS_PATH, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nruns 저장: {RUNS_PATH} ({len(runs)}행)")

    print("\n[채점] gpt-4o-mini judge")
    scores = score_answers(runs)

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        for s in scores:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"scores 저장: {SCORES_PATH}")

    write_results_uncovered(runs, scores)
    print(f"\n결과: {RESULTS_PATH}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    main()
