import json, sys
sys.stdout.reconfigure(encoding="utf-8")

IDK = ["확인할 수 없", "알 수 없", "모르겠", "정보가 없", "제공된 자료에서는"]
CITE = ["에 따르면", "출처:", "문서에", "안내에", "기준으로", "명시", "따라"]

def calc(run_file, score_file):
    runs, scores = [], []
    with open(run_file, encoding="utf-8") as f:
        for l in f: runs.append(json.loads(l))
    with open(score_file, encoding="utf-8") as f:
        for l in f: scores.append(json.loads(l))

    sm = {s["id"]: s for s in scores}
    q100s, hall, grnd, lats = [], [], [], []
    cite_hits = 0

    for r in runs:
        s = sm.get(r["id"], {})
        if "accuracy" not in s:
            continue
        q100s.append((s["accuracy"] + s["relevance"] + s["completeness"]) / 3 * 20)
        hall.append(s.get("hallucination", 0))
        grnd.append(1 if s.get("grounded") == "Y" else 0)
        if r.get("latency"):
            lats.append(r["latency"])
        ans = r.get("answer", "")
        if any(c in ans for c in CITE):
            cite_hits += 1

    n = len(q100s)
    lats_s = sorted(lats)
    p50 = lats_s[int(len(lats_s)*0.5)] if lats_s else 0
    p95 = lats_s[min(int(len(lats_s)*0.95), len(lats_s)-1)] if lats_s else 0

    # 경로별
    fast = [r for r in runs if r.get("path") == "fast"]
    deep = [r for r in runs if r.get("path") == "deep"]
    fast_lats = sorted(r["latency"] for r in fast if r.get("latency"))
    deep_lats = sorted(r["latency"] for r in deep if r.get("latency"))

    def pct(lst, p):
        if not lst: return 0
        return round(lst[min(int(len(lst)*p/100), len(lst)-1)], 2)

    idk = sum(1 for r in runs if any(p in r.get("answer","") for p in IDK))

    # 세그먼트별 점수
    seg = {}
    for st in ["cross_hop","complex","uncovered","dirty"]:
        vs = [(sm.get(r["id"],{}).get("accuracy",0)+sm.get(r["id"],{}).get("relevance",0)+sm.get(r["id"],{}).get("completeness",0))/3*20
              for r in runs if r.get("stratum")==st and "accuracy" in sm.get(r["id"],{})]
        seg[st] = round(sum(vs)/len(vs),1) if vs else 0

    return {
        "n": n, "score": round(sum(q100s)/n,1),
        "hall": round(sum(hall)/n*100,1),
        "grnd": round(sum(grnd)/n*100,1),
        "cite": round(cite_hits/len(runs)*100,1),
        "p50": round(p50,2), "p95": round(p95,2),
        "fast_p50": pct(fast_lats,50), "fast_p95": pct(fast_lats,95),
        "deep_p50": pct(deep_lats,50), "deep_p95": pct(deep_lats,95),
        "fast_n": len(fast), "deep_n": len(deep),
        "idk": round(idk/len(runs)*100,1),
        "seg": seg,
    }

e  = calc("experiments/results/runs_exaone_v3.jsonl",  "experiments/results/scores_exaone_v3.jsonl")
g  = calc("experiments/results/runs_v3.jsonl",          "experiments/results/scores_v3.jsonl")

print("=== EXAONE ===")
for k,v in e.items(): print(f"  {k}: {v}")
print("\n=== GPT-4o-mini ===")
for k,v in g.items(): print(f"  {k}: {v}")
