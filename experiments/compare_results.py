import json
from 실험.YHS_eval_questions_100 import EVAL_QUERIES

meta = {q['id']: q for q in EVAL_QUERIES}

def load(runs_path, scores_path):
    runs   = {json.loads(l)['id']: json.loads(l) for l in open(runs_path, encoding='utf-8')}
    scores = [json.loads(l) for l in open(scores_path, encoding='utf-8')]
    return runs, scores

def q100(s):
    return (s['accuracy'] + s['relevance'] + s['completeness']) / 3 * 20

def summarize(scores):
    by_stratum = {}
    halluc = 0
    for s in scores:
        st = s['stratum']
        by_stratum.setdefault(st, []).append(q100(s))
        halluc += s.get('hallucination', 0)
    total = [q100(s) for s in scores]
    return {
        'overall': sum(total)/len(total),
        'in_db':   sum(by_stratum.get('in_db',[0]))/max(len(by_stratum.get('in_db',[0])),1),
        'complex': sum(by_stratum.get('complex',[0]))/max(len(by_stratum.get('complex',[0])),1),
        'uncovered': sum(by_stratum.get('uncovered',[0]))/max(len(by_stratum.get('uncovered',[0])),1),
        'dirty':   sum(by_stratum.get('dirty',[0]))/max(len(by_stratum.get('dirty',[0])),1),
        'halluc_rate': halluc / len(scores) * 100,
        'n': len(scores),
    }

_, ex_scores = load('runs_exaone.jsonl', 'scores_exaone.jsonl')
_, gpt_scores = load('runs.jsonl', 'scores.jsonl')

ex  = summarize(ex_scores)
gpt = summarize(gpt_scores)

print("=" * 60)
print(f"{'지표':<20} {'EXAONE-3.5':>12} {'gpt-4o-mini':>12} {'차이':>8}")
print("-" * 60)
print(f"{'전체 품질 (100점)':<20} {ex['overall']:>11.1f}점 {gpt['overall']:>11.1f}점 {gpt['overall']-ex['overall']:>+7.1f}점")
print(f"{'  DB 수록 (38개)':<20} {ex['in_db']:>11.1f}점 {gpt['in_db']:>11.1f}점 {gpt['in_db']-ex['in_db']:>+7.1f}점")
print(f"{'  복합 질문 (26개)':<20} {ex['complex']:>11.1f}점 {gpt['complex']:>11.1f}점 {gpt['complex']-ex['complex']:>+7.1f}점")
print(f"{'  미수록 (12개)':<20} {ex['uncovered']:>11.1f}점 {gpt['uncovered']:>11.1f}점 {gpt['uncovered']-ex['uncovered']:>+7.1f}점")
print(f"{'  비격식 (4개)':<20} {ex['dirty']:>11.1f}점 {gpt['dirty']:>11.1f}점 {gpt['dirty']-ex['dirty']:>+7.1f}점")
print(f"{'환각률':<20} {ex['halluc_rate']:>11.1f}%  {gpt['halluc_rate']:>11.1f}%  {gpt['halluc_rate']-ex['halluc_rate']:>+7.1f}%p")
print("=" * 60)
