import json
from experiments.eval_sets.eval_questions_v2 import EVAL_QUERIES

meta = {q['id']: q for q in EVAL_QUERIES}

IDK_PHRASES = [
    "확인할 수 없", "확인되지 않", "알 수 없", "모릅니다", "모르겠",
    "정보가 없", "제공되지 않", "파악할 수 없", "안내드리기 어렵",
    "찾을 수 없", "공식 채널", "직접 문의", "담당 부서에 문의",
]

def is_idk(answer):
    return any(p in answer for p in IDK_PHRASES)

def q100(s): return (s['accuracy']+s['relevance']+s['completeness'])/3*20

for label, runs_path, scores_path in [
    ("EXAONE", "runs_exaone.jsonl", "scores_exaone.jsonl"),
    ("gpt-4o-mini+크롤링", "runs.jsonl", "scores.jsonl"),
]:
    runs   = [json.loads(l) for l in open(runs_path, encoding='utf-8')]
    scores = {json.loads(l)['id']: json.loads(l) for l in open(scores_path, encoding='utf-8')}

    total = len(runs)
    idk_all  = [r for r in runs if is_idk(r.get('answer',''))]
    idk_rate = len(idk_all)/total*100

    # 층별
    by_st = {}
    for r in runs:
        st = meta.get(r['id'], {}).get('stratum', r.get('stratum','?'))
        by_st.setdefault(st, []).append(r)

    print(f"\n{'='*55}")
    print(f"[{label}]  전체 모른다 비율: {len(idk_all)}/{total} = {idk_rate:.1f}%")
    print(f"{'층위':<14} {'전체':>5} {'모른다':>6} {'비율':>6}")
    print("-"*35)
    for st in ['in_db','complex','uncovered','dirty']:
        rows = by_st.get(st, [])
        idk_n = sum(1 for r in rows if is_idk(r.get('answer','')))
        print(f"  {st:<12} {len(rows):>5} {idk_n:>6} {idk_n/max(len(rows),1)*100:>5.0f}%")

    print()
    # 실제 모른다고 한 답변 중 점수 확인 (올바른 모른다 vs 틀린 모른다)
    print(f"  모른다고 한 {len(idk_all)}개 문항 품질점수:")
    for r in idk_all:
        s = scores.get(r['id'])
        if not s: continue
        st = meta.get(r['id'], {}).get('stratum','?')
        q = meta.get(r['id'], {}).get('query','')[:30]
        print(f"    [{st:<9}] {q100(s):5.1f}점  {q}")
