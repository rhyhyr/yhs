"""
experiments/make_claude_judge_prompts.py
runs_*.jsonl 파일을 읽어 Claude 채팅에 붙여넣을 수 있는 배치 판정 프롬프트를 생성.

사용법:
  python experiments/make_claude_judge_prompts.py [runs_파일.jsonl] [--batch-size N]

기본값:
  runs 파일: experiments/results/runs_v3b.jsonl  (GPT-4o-mini 답변 모델)
  batch_size: 10 (Claude 채팅 1회에 보낼 질문 수)

출력:
  claude_judge_batch_01.txt ... claude_judge_N.txt

각 파일을 Claude 채팅에 붙여넣으면 JSON 배열로 채점 결과를 돌려줌.
결과를 claude_judge_results_01.json ... 형식으로 저장한 뒤
  python experiments/make_claude_judge_prompts.py --aggregate
를 실행하면 집계 보고서를 출력한다.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_RUNS = "experiments/results/runs_v3b.jsonl"
OUT_DIR = Path("experiments/results/claude_judge")

JUDGE_PROMPT_HEADER = """\
당신은 엄격한 채점자다. 아래 항목들을 각각 평가하라.
각 항목에 대해 다음 규칙을 적용한다:
- accuracy: 정답 근거와 사실 일치 정도 (0~5)
- relevance: 질문에 직접, 질문과 같은 언어로 답하는 정도 (0~5)
- completeness: 핵심 항목 누락 없이 답한 정도 (0~5)
- hallucination: 근거에 없는 내용을 단정하면 1, 아니면 0
- grounded: 제시한 근거가 결론을 지지하면 "Y", 아니면 "N"
- gold가 "[크롤러]"로 시작하면: 시스템이 "확인할 수 없다" 또는 공식 채널 확인을 안내했으면 accuracy=5, relevance=5, completeness=5로 채점. 구체 날짜·정보를 제공하지 않았다는 이유로 감점하지 말 것.
- gold가 "[최신]" 또는 "[최신고시]"로 시작하면: 최신 정보나 관련 변경사항을 언급했으면 높게 채점.

아래 각 항목을 채점하여 JSON 배열로만 출력하라 (코드펜스·설명 금지).
출력 형식 예시:
[
  {"id": "q1", "accuracy": 4, "relevance": 5, "completeness": 4, "hallucination": 0, "grounded": "Y", "reason": "한 줄"},
  {"id": "q2", ...}
]

=== 채점 대상 ===
"""

ITEM_TEMPLATE = """\
--- 항목 {n} (id={id}) ---
[질문] {query}
[질문 언어] {lang}
[정답 근거(gold)] {gold}
[시스템 답변] {answer}
"""


def load_runs(path: str) -> list[dict]:
    runs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return runs


def make_batches(runs: list[dict], batch_size: int) -> list[list[dict]]:
    return [runs[i: i + batch_size] for i in range(0, len(runs), batch_size)]


def write_batch_prompt(batch: list[dict], batch_idx: int, out_dir: Path) -> Path:
    lines = [JUDGE_PROMPT_HEADER]
    for n, run in enumerate(batch, 1):
        if run.get("error") or not run.get("answer"):
            lines.append(f"--- 항목 {n} (id={run['id']}) ---\n[오류/빈 답변 → skip]\n")
        else:
            lines.append(ITEM_TEMPLATE.format(
                n=n,
                id=run["id"],
                query=run["query"],
                lang=run["lang"],
                gold=run["gold"],
                answer=run["answer"],
            ))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"claude_judge_batch_{batch_idx:02d}.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def aggregate_results(out_dir: Path, runs: list[dict]) -> None:
    """claude_judge_results_*.json 파일들을 모아 집계 보고서를 출력."""
    result_files = sorted(out_dir.glob("claude_judge_results_*.json"))
    if not result_files:
        print("[ERROR] claude_judge_results_*.json 파일이 없음.")
        print(f"  Claude 채팅 응답을 {out_dir}/claude_judge_results_01.json 형식으로 저장하세요.")
        return

    all_scores: list[dict] = []
    for f in result_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, list):
            all_scores.extend(data)
        else:
            print(f"[WARN] {f}가 배열 형식이 아님 — skip")

    score_map = {s["id"]: s for s in all_scores}
    run_map = {r["id"]: r for r in runs}

    strata: dict[str, list] = {"all": [], "cross_hop": [], "complex": [], "uncovered": [], "dirty": []}
    for r in runs:
        st = r.get("stratum", "")
        strata["all"].append(r["id"])
        if st in strata:
            strata[st].append(r["id"])

    def compute(ids: list[str]) -> dict:
        q_vals, h_vals, g_vals = [], [], []
        n_err = 0
        for rid in ids:
            s = score_map.get(rid, {})
            r = run_map.get(rid, {})
            if s.get("error") or r.get("error") or not r.get("answer"):
                n_err += 1
                continue
            if "accuracy" not in s:
                n_err += 1
                continue
            q_vals.append((s["accuracy"] + s["relevance"] + s["completeness"]) / 3.0)
            h_vals.append(int(s.get("hallucination", 0)))
            g_vals.append(1 if s.get("grounded") == "Y" else 0)
        n_total = len(ids)
        n_valid = n_total - n_err
        if not n_valid:
            return {"n_total": n_total, "n_valid": 0, "n_err": n_err}
        q_mean = sum(q_vals) / len(q_vals)
        h_mean = sum(h_vals) / len(h_vals)
        g_mean = sum(g_vals) / len(g_vals)
        return {
            "n_total": n_total, "n_valid": n_valid, "n_err": n_err,
            "quality_mean": round(q_mean, 3),
            "quality_100": round(q_mean * 20, 1),
            "halluc_rate": round(h_mean, 3),
            "grounded_rate": round(g_mean, 3),
        }

    agg = {k: compute(v) for k, v in strata.items()}
    a = agg["all"]

    print("\n=== Claude Judge 집계 결과 ===")
    print(f"전체: quality={a.get('quality_mean', 0):.3f} ({a.get('quality_100', 0):.1f}점/100) "
          f"| 환각률={a.get('halluc_rate', 0)*100:.1f}% "
          f"| 근거적합률={a.get('grounded_rate', 0)*100:.1f}% "
          f"| N={a['n_total']} (유효={a['n_valid']})")
    for seg, key in [("cross_hop", "cross_hop"), ("complex", "complex"), ("uncovered", "uncovered"), ("dirty", "dirty")]:
        s = agg[key]
        if s.get("n_valid", 0):
            print(f"  {seg}: {s['quality_100']:.1f}점 (N={s['n_total']})")

    out_path = out_dir / "claude_judge_aggregate.json"
    out_path.write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n집계 저장: {out_path}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_file", nargs="?", default=DEFAULT_RUNS)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--aggregate", action="store_true",
                        help="Claude 응답 저장 후 집계만 실행")
    args = parser.parse_args()

    runs = load_runs(args.runs_file)
    print(f"runs 로드: {len(runs)}개 ({args.runs_file})")

    if args.aggregate:
        aggregate_results(OUT_DIR, runs)
        return

    batches = make_batches(runs, args.batch_size)
    print(f"배치 수: {len(batches)} (배치당 최대 {args.batch_size}개)")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, batch in enumerate(batches, 1):
        path = write_batch_prompt(batch, i, OUT_DIR)
        print(f"  배치 {i:02d}: {path} ({len(batch)}개)")

    print(f"\n✓ 완료. {OUT_DIR}/ 디렉토리의 claude_judge_batch_*.txt 파일을")
    print("  Claude 채팅에 하나씩 붙여넣고, 응답을 각각")
    print(f"  {OUT_DIR}/claude_judge_results_01.json 형식으로 저장하세요.")
    print(f"\n채점 완료 후:\n  python experiments/make_claude_judge_prompts.py {args.runs_file} --aggregate")


if __name__ == "__main__":
    main()
