"""Verify saved real-run results without rerunning the translation model."""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from sacrebleu.metrics import BLEU
from translation_eval_en import DATA

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/translation_en'
data=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
rows=data['rows']
assert len(rows)==20
assert [r['id'] for r in rows]==list(range(1,21))
assert [(r['english_question'],r['reference']) for r in rows]==DATA
assert data['protocol']['dataset_sha256']=='96cbfcd0c667b45376b8302f94c93e4a18ebb93d6da31af2a613874c5a049a99'
assert hashlib.sha256(json.dumps(DATA,ensure_ascii=False).encode()).hexdigest()==data['protocol']['dataset_sha256']
assert hashlib.sha256((ROOT/'backend/src/yhs/rag/retrieval/translator.py').read_bytes()).hexdigest()==data['protocol']['service_file_sha256']
metric=BLEU(tokenize='char',smooth_method='exp',effective_order=True)
for r in rows:
    assert math.isclose(metric.sentence_score(r['system_translation'],[r['reference']]).score,r['bleu'],abs_tol=1e-9)
    assert math.isclose(r['final_score'],0.5*r['bleu']+50*r['bertscore'],abs_tol=1e-9)
    assert r['was_translated'] and r['detected_language']=='en' and r['response_language']=='en'
    assert not r['warnings']
for key,field in [('average_bleu','bleu'),('average_bertscore','bertscore'),('average_final_score','final_score')]:
    assert math.isclose(mean(r[field] for r in rows),data['summary'][key],abs_tol=1e-9)
assert sum(r['final_score']>=80 for r in rows)==data['summary']['above_80_count']==3
assert data['summary']['above_80_ratio']==3/20
assert not data['summary']['meets_average_80']
profile=json.loads((OUT/'profile-check.json').read_text(encoding='utf-8'))
assert profile['locale']=='en' and profile['profile']['languages']==['en']
assert profile['persisted_after_reload'] and not profile['page_errors']
message='PASS: 20 live translations; immutable references; unchanged service hash; recalculated BLEU, formula and averages; no fallback; English profile persisted.'
(OUT/'verification.txt').write_text(message+'\n',encoding='utf-8')
print(message)
