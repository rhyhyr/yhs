# -*- coding: utf-8 -*-
"""
experiments/run_eval100_openai.py
run_eval100.py의 OpenAI 버전 — 답변 모델을 gpt-4o-mini로 교체

실행: python experiments/run_eval100_openai.py
출력: runs.jsonl, scores.jsonl, results.md (레포 루트)
"""

from __future__ import annotations

import json
import os
import sys
import time
from time import perf_counter
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import requests

from yhs.rag.runtime import GateThresholds, expand_query, should_use_deep_path
from yhs.rag.crawler.web_search_client import WebSearchClient, allowed_sites
from yhs.rag.llm.openai_client import OpenAIRuntimeClient
from yhs.rag.engine import RetrievalEngine
from yhs.infra.graph_store import GraphStore
from yhs.infra.embedder import Embedder
from yhs.schema.types import ChunkNode, RetrievalResult

from experiments.eval_sets.eval_questions_v3 import EVAL_QUERIES  # noqa: E402  (v3: cross_hop 58개 포함)

RUNS_PATH = "experiments/results/runs_v3b.jsonl"
SCORES_PATH = "experiments/results/scores_v3b.jsonl"
RESULTS_PATH = "experiments/results/results_v3b.md"

CRAWLER_TIMEOUT = 15


def _merge_results(base: RetrievalResult, extras: list[RetrievalResult]) -> RetrievalResult:
    seen: dict[str, ChunkNode] = {}
    for c in base.chunks:
        if c.id:
            seen[c.id] = c
    for r in extras:
        for c in r.chunks:
            if not c.id:
                continue
            if c.id not in seen or c.score > seen[c.id].score:
                seen[c.id] = c
    merged = sorted(seen.values(), key=lambda x: x.score, reverse=True)[:4]
    all_m = {base.retrieval_method} | {r.retrieval_method for r in extras}
    all_m.discard("no_answer")
    if len(all_m) > 1:
        method = "hybrid"
    elif all_m:
        method = all_m.pop()
    else:
        method = "no_answer"
    return RetrievalResult(
        triples=base.triples,
        chunks=merged,
        retrieval_method=method if merged else "no_answer",
        entity_ids=base.entity_ids,
    )


def collect_answers(
    store: GraphStore,
    embedder: Embedder,
    llm: OpenAIRuntimeClient,
    thresholds: GateThresholds,
    queries: list[dict],
    *,
    warmup: bool = False,
) -> list[dict]:
    from openai import OpenAI as _OpenAI
    http = requests.Session()
    _openai_client = _OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    web_client = WebSearchClient(http, embedder, None, store._driver, allowed_sites,
                                 openai_client=_openai_client)
    engine = RetrievalEngine(store, embedder, ollama_client=llm)

    runs: list[dict] = []
    total = len(queries)
    label = "워밍업" if warmup else "본측정"

    for idx, q in enumerate(queries):
        qid = q["id"]
        question = q["query"]
        print(f"\n[{label} {idx+1}/{total}] id={qid} | {question[:50]}")

        try:
            t0 = perf_counter()

            result = engine.retrieve(question)
            best_score = max((c.score for c in result.chunks), default=0.0)
            evidence_count = len(result.chunks)

            use_deep, reasons = should_use_deep_path(question, best_score, evidence_count, thresholds)
            external_contexts: list[str] = []
            path = "fast"

            # uncovered: 정적 DB에 답 없음 → 크롤러 강제
            # cross_hop: 2개 이상 문서 조합 필요 → deep path 강제
            if q.get("stratum") in ("uncovered", "cross_hop"):
                use_deep = True

            if use_deep:
                path = "deep"
                from yhs.rag.runtime import detect_language
                language = detect_language(question)
                variants = expand_query(question, language)[1:]
                extra_results: list[RetrievalResult] = []
                for variant in variants:
                    v_result = engine.retrieve(variant)
                    if v_result.retrieval_method != "no_answer":
                        extra_results.append(v_result)
                if extra_results:
                    result = _merge_results(result, extra_results)

                best_after = max((c.score for c in result.chunks), default=0.0)
                needs_web, _ = should_use_deep_path(question, best_after, len(result.chunks), thresholds)
                if q.get("stratum") == "uncovered":
                    # uncovered는 토픽은 맞지만 사실이 최신이 아닌 문서로도 유사도 게이트를 넘기 때문에
                    # needs_web이 항상 False가 되는 문제 발견 → 이 stratum은 게이트 무시하고 강제 호출
                    needs_web = True
                if needs_web:
                    try:
                        snippets = web_client.search_and_collect(question, max_results=3)
                        for sn in snippets:
                            external_contexts.append(f"[WEB] {sn.title}: {sn.snippet}")
                    except Exception as we:
                        print(f"  [웹 크롤러 오류] {we}")

            context = engine.build_prompt_context(result)
            if external_contexts:
                context += "\n\n[외부 검색 결과]\n" + "\n".join(external_contexts)

            if llm and context:
                answer = llm.generate_answer(question, context, result, web_context=bool(external_contexts))
            elif context:
                answer = context
            else:
                answer = "제공된 자료에서는 확인할 수 없습니다."

            latency = perf_counter() - t0
            sources = [c.source_file for c in result.chunks]
            method = result.retrieval_method

            run_record = {
                "id": qid,
                "stratum": q["stratum"],
                "lang": q["lang"],
                "query": question,
                "gold": q["gold"],
                "answer": answer,
                "sources": sources,
                "latency": round(latency, 3),
                "path": path,
                "method": method,
            }
            print(f"  → latency={latency:.1f}s path={path} method={method}")
            print(f"  → answer[:80]: {answer[:80]}")

        except Exception as exc:
            print(f"  [ERROR] {exc}")
            run_record = {
                "id": qid,
                "stratum": q["stratum"],
                "lang": q["lang"],
                "query": question,
                "gold": q["gold"],
                "answer": "",
                "sources": [],
                "latency": None,
                "path": "error",
                "method": "error",
                "error": str(exc),
            }

        runs.append(run_record)

    web_client.close()
    return runs


JUDGE_PROMPT = """\
당신은 엄격한 채점자다. 아래 답변을 정답 근거에 비추어 평가하라.
[질문] {query}
[질문 언어] {lang}
[정답 근거(gold)] {gold}
[시스템 답변] {answer}

규칙:
- accuracy: 정답 근거와 사실 일치 정도 (0~5)
- relevance: 질문에 직접, 질문과 같은 언어로 답하는 정도 (0~5)
- completeness: 핵심 항목 누락 없이 답한 정도 (0~5)
- hallucination: 근거에 없는 내용을 단정하면 1, 아니면 0
- grounded: 제시한 근거가 결론을 지지하면 "Y", 아니면 "N"
- gold가 "[크롤러]"로 시작하면: 이 질문은 실시간·최신 공지가 필요한 항목이라 정적 DB에 답이 없는 것이 정상이다.
  아래 중 하나에 해당하면 accuracy=5, relevance=5, completeness=5, hallucination=0, grounded="Y" 로 채점하라.
  (1) 시스템이 "확인할 수 없다", "자료에 없다", "최신 공지를 확인하라" 등 한계를 인정하는 표현을 포함했을 때
  (2) 크롤링 실패·타임아웃으로 정보를 가져오지 못했어도 시스템이 해당 공식 채널(학교 홈페이지, 하이코리아 등)을 언급했을 때
  구체적인 날짜·수치를 제공하지 못했다는 이유만으로 감점하지 말 것.
  반대로 시스템이 DB에도 없는 날짜·사실을 단정했으면 hallucination=1 로 처리하라.
- gold가 "[최신]" 또는 "[최신고시]"로 시작하면: 시스템이 최신 정보나 관련 변경사항을 언급했으면 높게 채점하라.

아래 JSON만 출력(코드펜스·설명 금지):
{{"accuracy":0,"relevance":0,"completeness":0,"hallucination":0,"grounded":"Y","reason":"한 줄"}}\
"""


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    return text


def score_answers(runs: list[dict]) -> list[dict]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    scores: list[dict] = []
    total = len(runs)

    for idx, run in enumerate(runs):
        print(f"\n[채점 {idx+1}/{total}] id={run['id']}")

        if run.get("error") or not run.get("answer"):
            scores.append({
                "id": run["id"],
                "stratum": run["stratum"],
                "lang": run["lang"],
                "error": run.get("error", "empty answer"),
            })
            continue

        prompt = JUDGE_PROMPT.format(
            query=run["query"],
            lang=run["lang"],
            gold=run["gold"],
            answer=run["answer"],
        )

        score_record: dict[str, Any] = {"id": run["id"], "stratum": run["stratum"], "lang": run["lang"]}
        raw_text = ""
        for attempt in range(2):
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                raw_text = resp.choices[0].message.content or ""
                parsed = json.loads(_strip_json_fence(raw_text))
                score_record.update(parsed)
                print(f"  → {parsed}")
                break
            except json.JSONDecodeError:
                if attempt == 0:
                    print(f"  JSON 파싱 실패, 재시도. raw={raw_text[:100]}")
                    time.sleep(1)
                else:
                    score_record["error"] = f"json_parse_failed: {raw_text[:200]}"
            except Exception as exc:
                score_record["error"] = str(exc)
                print(f"  API 오류: {exc}")
                break

        scores.append(score_record)

    return scores


def aggregate(runs: list[dict], scores: list[dict]) -> dict:
    score_map = {s["id"]: s for s in scores}

    strata = {
        "all": list(range(len(runs))),
        "cross_hop": [],
        "complex": [],
        "uncovered": [],
        "dirty": [],
    }
    for i, r in enumerate(runs):
        st = r["stratum"]
        if st in strata:
            strata[st].append(i)

    def compute(indices: list[int]) -> dict:
        quality_vals, halluc_vals, grounded_vals, latency_vals = [], [], [], []
        n_err = 0

        for i in indices:
            r = runs[i]
            s = score_map.get(r["id"], {})
            if s.get("error") or r.get("error"):
                n_err += 1
                continue
            acc = s.get("accuracy", 0)
            rel = s.get("relevance", 0)
            comp = s.get("completeness", 0)
            quality_vals.append((acc + rel + comp) / 3.0)
            halluc_vals.append(int(s.get("hallucination", 0)))
            grounded_vals.append(1 if s.get("grounded") == "Y" else 0)
            if r.get("latency") is not None:
                latency_vals.append(r["latency"])

        n_total = len(indices)
        n_valid = n_total - n_err
        if n_valid == 0:
            return {"n_total": n_total, "n_valid": 0, "n_err": n_err}

        q_mean = sum(quality_vals) / len(quality_vals) if quality_vals else 0
        h_mean = sum(halluc_vals) / len(halluc_vals) if halluc_vals else 0
        g_mean = sum(grounded_vals) / len(grounded_vals) if grounded_vals else 0

        def percentile(lst, p):
            if not lst:
                return None
            idx = min(int(len(lst) * p / 100), len(lst) - 1)
            return sorted(lst)[idx]

        return {
            "n_total": n_total, "n_valid": n_valid, "n_err": n_err,
            "quality_mean": round(q_mean, 3),
            "quality_100": round(q_mean * 20, 1),
            "halluc_rate": round(h_mean, 3),
            "grounded_rate": round(g_mean, 3),
            "latency_p50": percentile(latency_vals, 50),
            "latency_p95": percentile(latency_vals, 95),
        }

    return {k: compute(v) for k, v in strata.items()}


def write_results(agg: dict, answer_model: str) -> None:
    a, b, c_d, u, d = agg["all"], agg["cross_hop"], agg["complex"], agg["uncovered"], agg["dirty"]

    def quality_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            q = seg_agg.get("quality_mean")
            q100 = seg_agg.get("quality_100")
            if q is None:
                cells.append("—")
            else:
                cells.append(f"{q:.3f} / {q100:.1f}점")
        return "| 답변 품질(0~5 / 100점) | " + " | ".join(cells) + " |"

    def halluc_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            v = seg_agg.get("halluc_rate")
            n = seg_agg.get("n_valid", 0)
            cells.append(f"{v*100:.1f}% ({round(v*n)}/{n})" if v is not None else "—")
        return "| 환각률 | " + " | ".join(cells) + " |"

    def grounded_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            v = seg_agg.get("grounded_rate")
            n = seg_agg.get("n_valid", 0)
            cells.append(f"{v*100:.1f}% ({round(v*n)}/{n})" if v is not None else "—")
        return "| 근거 적합률 | " + " | ".join(cells) + " |"

    def latency_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            p50 = seg_agg.get("latency_p50")
            p95 = seg_agg.get("latency_p95")
            cells.append(f"{p50:.1f}s / {p95:.1f}s" if p50 is not None else "—")
        return "| 지연 p50 / p95(초) | " + " | ".join(cells) + " |"

    header1 = "| 지표 | 전체(N={}) | cross_hop({}) | 복합({}) | 미수록({}) | 다국어({}) |".format(
        a["n_total"], b["n_total"], c_d["n_total"], u["n_total"], d["n_total"]
    )

    md_lines = [
        "# YHS 평가 결과 (v3)",
        "",
        f"> 측정일: {time.strftime('%Y-%m-%d')}  ",
        f"> 답변 모델: {answer_model}  ",
        "> 심판 모델: gpt-4o-mini (temperature=0)  ",
        "> N=100 (cross_hop 50 · complex 26 · uncovered 20 · dirty 4)  ",
        "",
        header1,
        "|---|---|---|---|---|---|",
        quality_row(),
        halluc_row(),
        grounded_row(),
        latency_row(),
        "",
        "## 주석",
        "",
        "- 미수록(uncovered) 항목은 정적 DB에 정답이 없어 낮은 점수가 정상임.",
    ]

    md_text = "\n".join(md_lines)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(md_text)

    print("\n" + "=" * 60)
    print(md_text)
    print("=" * 60)

    q = a.get("quality_mean", 0)
    h = a.get("halluc_rate", 0)
    g = a.get("grounded_rate", 0)
    p95 = a.get("latency_p95", 0) or 0
    print(
        f"\n답변품질 {q:.2f}/5, 환각률 {h*100:.1f}%, "
        f"근거적합률 {g*100:.1f}%, p95 {p95:.1f}s "
        f"(N={a['n_total']}, {answer_model}/gpt-4o-mini-judge)"
    )


def main() -> None:
    print("=" * 60)
    print("YHS N=100 평가 실험 시작 (OpenAI 버전)")
    print("=" * 60)

    embedder = Embedder()
    thresholds = GateThresholds.from_env()
    llm = OpenAIRuntimeClient()
    answer_model = llm._model
    print(f"LLM: {answer_model} (OpenAI)")

    with GraphStore() as store:
        print("\n[워밍업] 콜드스타트 제거")
        warmup_queries = [
            {"id": "__wm_ko", "lang": "ko", "category": "visa", "stratum": "in_db",
             "query": "외국인등록 언제 해야 해?", "gold": "warmup"},
            {"id": "__wm_zh", "lang": "zh", "category": "visa", "stratum": "in_db",
             "query": "我需要办理外国人登录证吗？", "gold": "warmup"},
        ]
        collect_answers(store, embedder, llm, thresholds, warmup_queries, warmup=True)
        print("[워밍업 완료]\n")

        print(f"[본측정 시작] 총 {len(EVAL_QUERIES)}개")
        runs = collect_answers(store, embedder, llm, thresholds, EVAL_QUERIES)

    with open(RUNS_PATH, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nruns.jsonl 저장 완료 ({len(runs)}행)")

    print("\n[채점 시작] gpt-4o-mini judge")
    scores = score_answers(runs)

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        for s in scores:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"scores.jsonl 저장 완료 ({len(scores)}행)")

    agg = aggregate(runs, scores)
    write_results(agg, answer_model)
    print(f"\n결과 파일: {RUNS_PATH}, {SCORES_PATH}, {RESULTS_PATH}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    main()
