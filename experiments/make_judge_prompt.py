"""
experiments/make_judge_prompt.py

runs.jsonl → 채점용 프롬프트 파일(judge_prompt_batch_*.txt) 생성.
AI에게 붙여넣으면 JSON 배열로 점수가 돌아오고,
그 결과를 judge_results_batch_*.json 으로 저장 후
python experiments/make_judge_prompt.py --aggregate 로 scores.jsonl + results.md 생성.

사용법:
  1) python experiments/make_judge_prompt.py
     → judge_prompt_batch_1.txt, judge_prompt_batch_2.txt ... 생성
  2) AI에게 각 파일 내용 붙여넣기 → JSON 배열 응답 복사
  3) 응답을 judge_results_batch_1.json, judge_results_batch_2.json ... 으로 저장
  4) python experiments/make_judge_prompt.py --aggregate
     → scores.jsonl + results.md 생성
"""

from __future__ import annotations

import json
import os
import sys
import time

RUNS_PATH = "runs.jsonl"
SCORES_PATH = "scores.jsonl"
RESULTS_PATH = "results.md"
BATCH_SIZE = 20  # 한 번에 넘길 항목 수 (너무 많으면 컨텍스트 초과)


JUDGE_SYSTEM = """\
당신은 엄격한 채점자입니다. 아래 지시에 따라 각 항목을 채점하세요.

채점 규칙:
- accuracy (0~5): 정답 근거(gold)와 사실 일치 정도
- relevance (0~5): 질문에 직접, 질문과 같은 언어로 답하는 정도
- completeness (0~5): 핵심 항목 누락 없이 답한 정도
- hallucination (0 또는 1): 근거에 없는 내용을 단정하면 1, 아니면 0
- grounded ("Y" 또는 "N"): 제시한 근거가 결론을 지지하면 "Y"
- gold가 "[크롤러]"로 시작하면: 구체 정답 대신 '최신 확인 안내'가 정답. 구체 수치 단정 시 hallucination=1.
- reason: 채점 근거 한 줄 (한국어)

출력 형식: 아래 JSON 배열만 출력하세요. 코드펜스·설명·머릿말 없이 [ 로 시작해서 ] 로 끝내세요.
[
  {"id":"...", "accuracy":0, "relevance":0, "completeness":0, "hallucination":0, "grounded":"Y", "reason":"..."},
  ...
]
"""

ITEM_TEMPLATE = """\
---
id: {id}
lang: {lang}
질문: {query}
정답 근거(gold): {gold}
시스템 답변: {answer}
"""


def make_prompts() -> None:
    runs = [json.loads(line) for line in open(RUNS_PATH, encoding="utf-8")]
    print(f"runs.jsonl 로드: {len(runs)}행")

    batches = [runs[i:i + BATCH_SIZE] for i in range(0, len(runs), BATCH_SIZE)]
    print(f"배치 수: {len(batches)} (배치당 최대 {BATCH_SIZE}개)")

    for bi, batch in enumerate(batches, 1):
        items_text = "\n".join(
            ITEM_TEMPLATE.format(
                id=r["id"],
                lang=r["lang"],
                query=r["query"],
                gold=r["gold"],
                answer=r["answer"],
            )
            for r in batch
        )
        ids = [r["id"] for r in batch]
        prompt_text = (
            JUDGE_SYSTEM
            + f"\n\n아래 {len(batch)}개 항목을 채점하세요 (id 순서 유지):\n\n"
            + items_text
            + f"\n\n위 {len(batch)}개 항목 채점 결과를 JSON 배열로 출력하세요."
        )
        fname = f"judge_prompt_batch_{bi}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        print(f"  저장: {fname} ({len(batch)}개, ids: {ids[0]}~{ids[-1]})")

    print(
        f"\n완료. judge_prompt_batch_1.txt ~ judge_prompt_batch_{len(batches)}.txt 생성됨.\n"
        "각 파일을 AI에게 붙여넣고 응답을 judge_results_batch_1.json ~ "
        f"judge_results_batch_{len(batches)}.json 으로 저장 후\n"
        "python experiments/make_judge_prompt.py --aggregate 실행."
    )


# ── 집계 ─────────────────────────────────────────────────────────────────────

def aggregate_and_report() -> None:
    # 1) scores.jsonl 재구성
    runs = [json.loads(line) for line in open(RUNS_PATH, encoding="utf-8")]
    run_map = {r["id"]: r for r in runs}

    all_scores: list[dict] = []
    bi = 1
    while True:
        fname = f"judge_results_batch_{bi}.json"
        if not os.path.exists(fname):
            break
        raw = open(fname, encoding="utf-8").read().strip()
        # 코드펜스 제거
        if raw.startswith("```"):
            lines = raw.splitlines()
            end = next((i for i, l in enumerate(lines) if l.strip() == "```" and i > 0), len(lines))
            raw = "\n".join(lines[1:end]).strip()
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[ERROR] {fname} JSON 파싱 실패: {e}")
            print("  파일 내용 앞부분:", raw[:300])
            sys.exit(1)
        for item in items:
            qid = item["id"]
            r = run_map.get(qid, {})
            all_scores.append({
                "id": qid,
                "stratum": r.get("stratum", ""),
                "lang": r.get("lang", ""),
                **{k: item[k] for k in ("accuracy", "relevance", "completeness", "hallucination", "grounded", "reason") if k in item},
            })
        print(f"  {fname} 로드: {len(items)}개")
        bi += 1

    if not all_scores:
        print("judge_results_batch_*.json 파일이 없습니다.")
        sys.exit(1)

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        for s in all_scores:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"\nscores.jsonl 저장: {len(all_scores)}행")

    # 2) 집계
    score_map = {s["id"]: s for s in all_scores}
    strata = {"all": [], "in_db": [], "complex": [], "uncovered": [], "dirty": []}
    for i, r in enumerate(runs):
        strata["all"].append(i)
        st = r["stratum"]
        if st in strata:
            strata[st].append(i)

    def compute(indices):
        q_vals, h_vals, g_vals, lat_vals = [], [], [], []
        n_err = 0
        for i in indices:
            r = runs[i]
            s = score_map.get(r["id"], {})
            if s.get("error") or r.get("error"):
                n_err += 1
                continue
            if "accuracy" not in s:
                n_err += 1
                continue
            q_vals.append((s["accuracy"] + s["relevance"] + s["completeness"]) / 3.0)
            h_vals.append(int(s.get("hallucination", 0)))
            g_vals.append(1 if s.get("grounded") == "Y" else 0)
            if r.get("latency") is not None:
                lat_vals.append(r["latency"])
        n_valid = len(indices) - n_err
        if not n_valid:
            return {"n_total": len(indices), "n_valid": 0, "n_err": n_err}
        def pct(lst, p):
            if not lst:
                return None
            lst = sorted(lst)
            return lst[min(int(len(lst) * p / 100), len(lst)-1)]
        qm = sum(q_vals)/len(q_vals) if q_vals else 0
        hm = sum(h_vals)/len(h_vals) if h_vals else 0
        gm = sum(g_vals)/len(g_vals) if g_vals else 0
        return {
            "n_total": len(indices), "n_valid": n_valid, "n_err": n_err,
            "quality_mean": round(qm, 3), "quality_100": round(qm*20, 1),
            "halluc_rate": round(hm, 3), "grounded_rate": round(gm, 3),
            "latency_p50": pct(lat_vals, 50), "latency_p95": pct(lat_vals, 95),
        }

    agg = {k: compute(v) for k, v in strata.items()}

    # 3) results.md
    a, b, c, u, d = agg["all"], agg["in_db"], agg["complex"], agg["uncovered"], agg["dirty"]
    segs = [a, b, c, u, d]

    def qrow():
        cells = [f"{s.get('quality_mean','—'):.3f} / {s.get('quality_100','—'):.1f}점" if s.get("quality_mean") is not None else "—" for s in segs]
        return "| 답변 품질(0~5 / 100점) | " + " | ".join(cells) + " |"

    def hrow():
        cells = []
        for s in segs:
            v = s.get("halluc_rate")
            n = s.get("n_valid", 0)
            cells.append(f"{v*100:.1f}% ({round(v*n)}/{n})" if v is not None else "—")
        return "| 환각률 | " + " | ".join(cells) + " |"

    def grow():
        cells = []
        for s in segs:
            v = s.get("grounded_rate")
            n = s.get("n_valid", 0)
            cells.append(f"{v*100:.1f}% ({round(v*n)}/{n})" if v is not None else "—")
        return "| 근거 적합률 | " + " | ".join(cells) + " |"

    def lrow():
        cells = [f"{s.get('latency_p50','—'):.1f}s / {s.get('latency_p95','—'):.1f}s" if s.get("latency_p50") is not None else "—" for s in segs]
        return "| 지연 p50 / p95(초) | " + " | ".join(cells) + " |"

    header = f"| 지표 | 전체(N={a['n_total']}) | 표준({b['n_total']}) | 복합({c['n_total']}) | 미수록({u['n_total']}) | 다국어({d['n_total']}) |"
    md = "\n".join([
        "# YHS 평가 결과",
        "",
        f"> 측정일: {time.strftime('%Y-%m-%d')}  ",
        "> 답변 모델: EXAONE 3.5 7.8b (Ollama)  ",
        "> 심판 모델: (수동 채점, 동일 루브릭)  ",
        f"> N=100 (표준 {b['n_total']} · 복합 {c['n_total']} · 미수록 {u['n_total']} · 다국어 {d['n_total']})  ",
        "",
        header,
        "|---|---|---|---|---|---|",
        qrow(), hrow(), grow(), lrow(),
        "",
        "## 주석",
        "",
        "- 미수록(uncovered) 항목은 정적 DB에 정답이 없어 낮은 점수가 정상임.",
        "- EXAONE 기준 재측정값. 구 70%(Gemini·in-DB 기준)와 직접 비교 불가.",
        "- 심판: 실험계획 루브릭 그대로 적용.",
    ])
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(md)

    print("\n" + "=" * 60)
    print(md)
    print("=" * 60)
    qa = a.get("quality_mean", 0) or 0
    ha = a.get("halluc_rate", 0) or 0
    ga = a.get("grounded_rate", 0) or 0
    p95 = a.get("latency_p95") or 0
    print(
        f"\n답변품질 {qa:.2f}/5, 환각률 {ha*100:.1f}%, "
        f"근거적합률 {ga*100:.1f}%, p95 {p95:.1f}s "
        f"(N={a['n_total']}, EXAONE/수동judge)"
    )


if __name__ == "__main__":
    if "--aggregate" in sys.argv:
        aggregate_and_report()
    else:
        make_prompts()
