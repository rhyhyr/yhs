from __future__ import annotations

import argparse
import json
import time
from typing import Any

from hybrid_query_agent import HybridQueryAgent
from student_agent import SessionStore, StudentAgent


SAMPLE_QUESTIONS = [
    "비자 연장 기한이 언제까지인가요?",
    "D-2와 D-4 비자 연장 절차 차이가 뭐야?",
    "Why was my extension application rejected?",
    "哪些情况可以例外处理签证延期？",
]


def run_student_agent(questions: list[str]) -> list[dict[str, Any]]:
    agent = StudentAgent()
    session = SessionStore()
    user_id = "regression_user"
    rows: list[dict[str, Any]] = []

    try:
        for q in questions:
            profile, history = session.get(user_id)
            t0 = time.perf_counter()
            res = agent.ask(q, profile, history)
            elapsed = round(time.perf_counter() - t0, 3)
            session.save(user_id, res["profile"], res["history"])
            rows.append(
                {
                    "agent": "student_agent",
                    "query": q,
                    "answered": bool(res.get("answered", False)),
                    "path": res.get("path", "fast"),
                    "best_score": float(res.get("best_score", 0.0)),
                    "elapsed_sec": elapsed,
                    "sla_ok": elapsed <= (5.0 if res.get("path", "fast") == "fast" else 10.0),
                }
            )
    finally:
        agent.close()
    return rows


def run_hybrid_agent(questions: list[str]) -> list[dict[str, Any]]:
    agent = HybridQueryAgent()
    rows: list[dict[str, Any]] = []

    try:
        for q in questions:
            t0 = time.perf_counter()
            res = agent.ask(q)
            elapsed = round(time.perf_counter() - t0, 3)
            rows.append(
                {
                    "agent": "hybrid_query_agent",
                    "query": q,
                    "answered": bool(res.get("answered", False)),
                    "path": res.get("path", "fast"),
                    "best_score": float(res.get("best_score", 0.0)),
                    "elapsed_sec": elapsed,
                    "sla_ok": elapsed <= (5.0 if res.get("path", "fast") == "fast" else 10.0),
                }
            )
    finally:
        agent.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple regression runner for 1-hop/2-hop QA")
    parser.add_argument("--agent", choices=["student", "hybrid", "both"], default="both")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    if args.agent in {"student", "both"}:
        rows.extend(run_student_agent(SAMPLE_QUESTIONS))
    if args.agent in {"hybrid", "both"}:
        rows.extend(run_hybrid_agent(SAMPLE_QUESTIONS))

    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
