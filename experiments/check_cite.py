import json, sys
sys.stdout.reconfigure(encoding="utf-8")

CITE = ["에 따르면", "출처:", "문서에", "안내에", "기준으로", "명시", "따라"]

def check(run_file, label):
    runs = [json.loads(l) for l in open(run_file, encoding="utf-8")]
    hits = []
    for r in runs:
        ans = r.get("answer", "")
        matched = [c for c in CITE if c in ans]
        hits.append((r["id"], bool(matched), matched, ans[:80]))
    n_hit = sum(1 for _, h, _, _ in hits if h)
    print(f"\n=== {label} ===")
    print(f"인용 표현 있음: {n_hit}/{len(runs)} = {n_hit/len(runs)*100:.1f}%")
    print("\n[인용 표현 없는 예시 5개]")
    no_hit = [(id_, ans) for id_, h, _, ans in hits if not h][:5]
    for id_, ans in no_hit:
        print(f"  {id_}: {ans}")
    print("\n[인용 표현 있는 예시 3개]")
    yes_hit = [(id_, m, ans) for id_, h, m, ans in hits if h][:3]
    for id_, m, ans in yes_hit:
        print(f"  {id_} {m}: {ans}")

check("experiments/results/runs_exaone_v3.jsonl", "EXAONE v3")
check("experiments/results/runs_v3.jsonl", "GPT-4o-mini v3")
