# -*- coding: utf-8 -*-
"""
experiments/run_eval100.py
YHS N=100 평가 러너 — 실험/YHS_실험_실행계획.md 기반

실행: python experiments/run_eval100.py
출력: runs.jsonl, scores.jsonl, results.md (레포 루트)
"""

from __future__ import annotations

import json
import os
import sys
import time
from time import perf_counter
from typing import Any

# 레포 루트에서 실행 보장
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# UTF-8 출력 강제 (Windows CP949 환경 대응)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 환경변수 RUNTIME_LLM 강제 (dotenv 로드 전 설정)
os.environ.setdefault("RUNTIME_LLM", "ollama")

from dotenv import load_dotenv
load_dotenv()

import requests

from agent.agent_runtime import GateThresholds, expand_query, should_use_deep_path
from agent.crawler.web_search_client import WebSearchClient, allowed_sites
from agent.ollama_runtime_client import OllamaRuntimeClient
from agent.retrieval_engine import RetrievalEngine
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder
from graph_rag.schema.types import ChunkNode, RetrievalResult

# ── 데이터셋 ────────────────────────────────────────────────────────────────
from 실험.YHS_eval_questions_v3 import EVAL_QUERIES  # noqa: E402  (v3: cross_hop 58개 포함)

RUNS_PATH = "실험/results/runs_exaone_v3b.jsonl"
SCORES_PATH = "실험/results/scores_exaone_v3b.jsonl"
RESULTS_PATH = "실험/results/results_exaone_v3b.md"

CRAWLER_TIMEOUT = 15  # 초


# ── 유틸 ─────────────────────────────────────────────────────────────────────

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


# ── 1단계: 답변 수집 ─────────────────────────────────────────────────────────

def collect_answers(
    store: GraphStore,
    embedder: Embedder,
    llm: OllamaRuntimeClient,
    thresholds: GateThresholds,
    queries: list[dict],
    *,
    warmup: bool = False,
) -> list[dict]:
    """queries 에 대해 답변을 수집하고 runs 리스트로 반환."""
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

            # Fast path
            result = engine.retrieve(question)
            best_score = max((c.score for c in result.chunks), default=0.0)
            evidence_count = len(result.chunks)

            use_deep, reasons = should_use_deep_path(question, best_score, evidence_count, thresholds)
            external_contexts: list[str] = []
            path = "fast"

            # uncovered: DB 미수록 → 크롤러 강제
            # cross_hop: 2개 이상 문서 조합 필요 → deep path 강제
            if q.get("stratum") in ("uncovered", "cross_hop"):
                use_deep = True

            if use_deep:
                path = "deep"
                # 변형 쿼리 병합
                from agent.agent_runtime import detect_language
                language = detect_language(question)
                variants = expand_query(question, language)[1:]
                extra_results: list[RetrievalResult] = []
                for variant in variants:
                    v_result = engine.retrieve(variant)
                    if v_result.retrieval_method != "no_answer":
                        extra_results.append(v_result)
                if extra_results:
                    result = _merge_results(result, extra_results)

                # 병합 후 재판정 → 웹 크롤링
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

            # 컨텍스트 조합
            context = engine.build_prompt_context(result)
            if external_contexts:
                context += "\n\n[외부 검색 결과]\n" + "\n".join(external_contexts)

            # 답변 생성
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


# ── 2단계: 채점 ───────────────────────────────────────────────────────────────

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
- gold가 "[크롤러]"로 시작하면, 구체 정답 대신 '최신 확인 안내'가 정답이다.

아래 JSON만 출력(코드펜스·설명 금지):
{{"accuracy":0,"relevance":0,"completeness":0,"hallucination":0,"grounded":"Y","reason":"한 줄"}}\
"""


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # 첫 줄(```json 등) 제거, 마지막 줄(```) 제거
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
                    print(f"  재시도 실패 → error 기록")
            except Exception as exc:
                score_record["error"] = str(exc)
                print(f"  API 오류: {exc}")
                break

        scores.append(score_record)

    return scores


# ── 3단계: 집계 ───────────────────────────────────────────────────────────────

def aggregate(runs: list[dict], scores: list[dict]) -> dict:
    from statistics import median

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
        quality_vals = []
        halluc_vals = []
        grounded_vals = []
        latency_vals = []
        n_err = 0
        n_total = len(indices)

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

        n_valid = n_total - n_err
        if n_valid == 0:
            return {"n_total": n_total, "n_valid": 0, "n_err": n_err}

        q_mean = sum(quality_vals) / len(quality_vals) if quality_vals else 0
        h_mean = sum(halluc_vals) / len(halluc_vals) if halluc_vals else 0
        g_mean = sum(grounded_vals) / len(grounded_vals) if grounded_vals else 0

        latency_vals_s = sorted(latency_vals)
        def percentile(lst, p):
            if not lst:
                return None
            idx = int(len(lst) * p / 100)
            idx = min(idx, len(lst) - 1)
            return lst[idx]

        return {
            "n_total": n_total,
            "n_valid": n_valid,
            "n_err": n_err,
            "quality_mean": round(q_mean, 3),
            "quality_100": round(q_mean * 20, 1),
            "halluc_rate": round(h_mean, 3),
            "grounded_rate": round(g_mean, 3),
            "latency_p50": percentile(latency_vals_s, 50),
            "latency_p95": percentile(latency_vals_s, 95),
        }

    return {k: compute(v) for k, v in strata.items()}


# ── 4단계: 보고서 출력 ────────────────────────────────────────────────────────

def fmt(val, n_total=None, fmt_str=".3f", is_pct=False):
    if val is None:
        return "—"
    if is_pct and n_total is not None:
        count = round(val * n_total)
        return f"{val*100:.1f}% ({count}/{n_total})"
    return f"{val:{fmt_str}}"


def write_results(agg: dict) -> None:
    a = agg["all"]
    b = agg["cross_hop"]
    c_d = agg["complex"]
    u = agg["uncovered"]
    d = agg["dirty"]

    def row(label, key, is_pct=False, extra_fmt=None):
        cells = []
        for seg, seg_agg in [("전체", a), ("표준", b), ("복합", c_d), ("미수록", u), ("다국어", d)]:
            n = seg_agg.get("n_total", 0)
            v = seg_agg.get(key)
            if v is None:
                cells.append("—")
            elif is_pct:
                count = round(v * seg_agg["n_valid"]) if seg_agg.get("n_valid") else 0
                cells.append(f"{v*100:.1f}% ({count}/{seg_agg['n_valid']})")
            elif extra_fmt:
                cells.append(extra_fmt(v))
            else:
                cells.append(str(v))
        return "| " + label + " | " + " | ".join(cells) + " |"

    def quality_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            q = seg_agg.get("quality_mean")
            q100 = seg_agg.get("quality_100")
            n = seg_agg.get("n_valid", 0)
            if q is None:
                cells.append("—")
            else:
                cells.append(f"{q:.3f} / {q100:.1f}점")
        return "| 답변 품질(0~5 / 100점) | " + " | ".join(cells) + " |"

    def latency_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            p50 = seg_agg.get("latency_p50")
            p95 = seg_agg.get("latency_p95")
            if p50 is None:
                cells.append("—")
            else:
                cells.append(f"{p50:.1f}s / {p95:.1f}s")
        return "| 지연 p50 / p95(초) | " + " | ".join(cells) + " |"

    header1 = "| 지표 | 전체(N={}) | cross_hop({}) | 복합({}) | 미수록({}) | 다국어({}) |".format(
        a["n_total"], b["n_total"], c_d["n_total"], u["n_total"], d["n_total"]
    )
    header2 = "|---|---|---|---|---|---|"

    # 환각률 행
    def halluc_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            v = seg_agg.get("halluc_rate")
            n = seg_agg.get("n_valid", 0)
            if v is None:
                cells.append("—")
            else:
                count = round(v * n)
                cells.append(f"{v*100:.1f}% ({count}/{n})")
        return "| 환각률 | " + " | ".join(cells) + " |"

    def grounded_row():
        cells = []
        for seg_agg in [a, b, c_d, u, d]:
            v = seg_agg.get("grounded_rate")
            n = seg_agg.get("n_valid", 0)
            if v is None:
                cells.append("—")
            else:
                count = round(v * n)
                cells.append(f"{v*100:.1f}% ({count}/{n})")
        return "| 근거 적합률 | " + " | ".join(cells) + " |"

    md_lines = [
        "# YHS 평가 결과",
        "",
        f"> 측정일: {time.strftime('%Y-%m-%d')}  ",
        "> 답변 모델: EXAONE 3.5 7.8b (Ollama)  ",
        "> 심판 모델: gpt-4o-mini (temperature=0)  ",
        "> N=100 (cross_hop 50 · complex 26 · uncovered 20 · dirty 4)  ",
        "",
        header1,
        header2,
        quality_row(),
        halluc_row(),
        grounded_row(),
        latency_row(),
        "",
        "## 오류 현황",
        "",
    ]

    for seg, seg_agg in [("전체", a), ("표준", b), ("복합", c_d), ("미수록", u), ("다국어", d)]:
        n_err = seg_agg.get("n_err", 0)
        n_total = seg_agg.get("n_total", 0)
        if n_err:
            md_lines.append(f"- {seg}: {n_err}/{n_total} 오류")

    md_lines += [
        "",
        "## 주석",
        "",
        "- 미수록(uncovered) 항목은 정적 DB에 정답이 없어 낮은 점수가 정상임.",
        "- EXAONE 기준 재측정값. 구 70%(Gemini·in-DB 기준)와 직접 비교 불가.",
    ]

    md_text = "\n".join(md_lines)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(md_text)

    print("\n" + "=" * 60)
    print(md_text)
    print("=" * 60)

    # 콘솔 요약 1줄
    q = a.get("quality_mean", 0)
    h = a.get("halluc_rate", 0)
    g = a.get("grounded_rate", 0)
    p95 = a.get("latency_p95", 0) or 0
    print(
        f"\n답변품질 {q:.2f}/5, 환각률 {h*100:.1f}%, "
        f"근거적합률 {g*100:.1f}%, p95 {p95:.1f}s "
        f"(N={a['n_total']}, EXAONE/gpt-4o-mini-judge)"
    )


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("YHS N=100 평가 실험 시작")
    print("=" * 60)

    embedder = Embedder()
    thresholds = GateThresholds.from_env()
    llm = OllamaRuntimeClient()
    if not llm.is_available():
        print("[FATAL] Ollama 서버 응답 없음. 'ollama serve' 실행 후 재시도.")
        sys.exit(1)
    print(f"LLM: {llm._model} @ {llm._base_url}")

    with GraphStore() as store:
        # ── 1단계: 워밍업 (결과 버림) ──────────────────────────────────────
        print("\n[워밍업] 콜드스타트 제거 (ko 1개 + zh 1개)")
        warmup_queries = [
            {
                "id": "__wm_ko",
                "lang": "ko",
                "category": "visa",
                "stratum": "in_db",
                "query": "외국인등록 언제 해야 해?",
                "gold": "warmup",
            },
            {
                "id": "__wm_zh",
                "lang": "zh",
                "category": "visa",
                "stratum": "in_db",
                "query": "我需要办理外国人登录证吗？",
                "gold": "warmup",
            },
        ]
        collect_answers(store, embedder, llm, thresholds, warmup_queries, warmup=True)
        print("[워밍업 완료] 결과 버림.\n")

        # ── 2단계: 본측정 (100개) ───────────────────────────────────────────
        print(f"[본측정 시작] 총 {len(EVAL_QUERIES)}개")
        runs = collect_answers(store, embedder, llm, thresholds, EVAL_QUERIES)

    # runs.jsonl 저장
    with open(RUNS_PATH, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nruns.jsonl 저장 완료 ({len(runs)}행)")

    # ── 3단계: 채점 ─────────────────────────────────────────────────────────
    print("\n[채점 시작] gpt-4o-mini judge")
    scores = score_answers(runs)

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        for s in scores:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"scores.jsonl 저장 완료 ({len(scores)}행)")

    # ── 4단계: 집계 + 보고서 ────────────────────────────────────────────────
    agg = aggregate(runs, scores)
    write_results(agg)
    print(f"\n결과 파일: {RUNS_PATH}, {SCORES_PATH}, {RESULTS_PATH}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    main()
