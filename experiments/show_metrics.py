import json
import statistics

from experiments.eval_sets.eval_questions_v2 import EVAL_QUERIES

meta = {q['id']: q for q in EVAL_QUERIES}

def load(runs_path, scores_path):
    runs   = [json.loads(l) for l in open(runs_path, encoding='utf-8')]
    scores = [json.loads(l) for l in open(scores_path, encoding='utf-8')]
    return runs, scores

CITE_PHRASES = ["에 따르면", "에 의하면", "문서에", "안내에 따라", "기준에 따르면",
                "규정에 따르면", "자료에 따르면", "출입국", "하이코리아", "보건복지부"]

def has_citation(answer):
    return any(p in answer for p in CITE_PHRASES)

for label, rp, sp in [
    ("EXAONE", "runs_exaone.jsonl", "scores_exaone.jsonl"),
    ("gpt-4o-mini+크롤링", "runs.jsonl", "scores.jsonl"),
]:
    runs, scores = load(rp, sp)
    scores_map = {s['id']: s for s in scores}

    print(f"\n{'='*55}")
    print(f"[{label}]")

    # 1. 근거 적합률 (grounded Y)
    grounded = [s for s in scores if s.get('grounded') == 'Y']
    gr_rate = len(grounded) / len(scores) * 100
    print(f"\n① 근거 적합률: {len(grounded)}/{len(scores)} = {gr_rate:.1f}%")
    by_st = {}
    for s in scores:
        by_st.setdefault(s['stratum'], []).append(s.get('grounded') == 'Y')
    for st in ['in_db','complex','uncovered','dirty']:
        vals = by_st.get(st, [])
        print(f"   {st:<12}: {sum(vals)}/{len(vals)} = {sum(vals)/max(len(vals),1)*100:.0f}%")

    # 2. 근거 커버리지 (proxy: 답변에 인용 표현 있는 비율 - 복합/in_db만)
    eligible = [r for r in runs if meta.get(r['id'], {}).get('stratum') in ('in_db', 'complex')]
    cited = [r for r in eligible if has_citation(r.get('answer', ''))]
    cc_rate = len(cited) / max(len(eligible), 1) * 100
    print(f"\n② 근거 커버리지(proxy): {len(cited)}/{len(eligible)} = {cc_rate:.1f}%")
    print("   (인용 표현 포함 답변 비율 — 사람 검토 필요)")

    # 3. 최신성 정답률 → 미측정
    print("\n③ 최신성 정답률: 미측정 (FRESHNESS_PAIRS 실행 필요)")

    # 4. 지연시간
    latencies = [r['latency'] for r in runs if r.get('latency')]
    lat_sorted = sorted(latencies)
    n = len(lat_sorted)
    p50 = lat_sorted[int(n * 0.5)]
    p95 = lat_sorted[int(n * 0.95)]
    print(f"\n④ 지연시간 (n={n})")
    print(f"   p50: {p50:.2f}s  /  p95: {p95:.2f}s  /  평균: {statistics.mean(latencies):.2f}s")

    # path별
    fast_lat = [r['latency'] for r in runs if r.get('path') == 'fast' and r.get('latency')]
    deep_lat = [r['latency'] for r in runs if r.get('path') == 'deep' and r.get('latency')]
    if fast_lat:
        print(f"   fast path: 평균 {statistics.mean(fast_lat):.2f}s (n={len(fast_lat)})")
    if deep_lat:
        print(f"   deep path: 평균 {statistics.mean(deep_lat):.2f}s (n={len(deep_lat)})")

    # 5. 비용 & 캐시
    fast_n = sum(1 for r in runs if r.get('path') == 'fast')
    deep_n = sum(1 for r in runs if r.get('path') == 'deep')
    print("\n⑤ 비용·캐시: 토큰 수 미기록 → 정밀 측정 불가")
    print(f"   fast(DB만): {fast_n}건  /  deep(크롤링+확장): {deep_n}건")
    print("   (deep는 fast 대비 LLM 호출량·비용 증가)")
