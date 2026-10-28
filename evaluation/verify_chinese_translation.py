"""Independent checks for the Chinese dataset, actual output pairs and stored metrics."""
import json, math, hashlib
from pathlib import Path
from sacrebleu.metrics import BLEU
OUT=Path(__file__).resolve().parent/'results'/'translation_e2e_zh'

def main():
    d=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    protocol=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    collection=json.loads((OUT/'collection.json').read_text(encoding='utf-8'))
    refs=json.loads((OUT.parent/'translation_e2e'/'results.json').read_text(encoding='utf-8'))['rows']
    rows=d['rows']; by_id={r['id']:r for r in collection}
    assert [r['id'] for r in rows]==list(range(1,21))
    bleu=BLEU(tokenize='char',smooth_method='exp',effective_order=True)
    for r,reference in zip(rows,refs):
        raw=by_id[r['id']]
        assert r['status']=='ok'
        assert r['chinese_question']==protocol['dataset'][r['id']-1]['chinese_question']
        assert r['reference']==reference['reference']
        assert r['system_translation']==raw['system_translation']
        assert r['chinese_final_answer']==raw['api_response']['answer']==raw['chinese_final_answer']
        assert math.isclose(r['question_semantic_score'],r['bertscore']*100,abs_tol=1e-9)
        assert math.isclose(r['smoothed_bleu'],bleu.sentence_score(r['system_translation'],[r['reference']]).score,abs_tol=1e-9)
        if r['answer_similarity_score'] is not None:
            assert r['korean_source_answer']==raw['translation_events'][-1]['korean_source']
            assert raw['translation_events'][-1]['target_language']=='zh'
            assert raw['translation_events'][-1]['chinese_translation']==r['chinese_final_answer']
            assert math.isclose(r['answer_similarity_score'],r['answer_f1']*100,abs_tol=1e-9)
    s=d['summary']
    pairs=[r for r in rows if r['answer_similarity_score'] is not None]
    assert math.isclose(s['question_average'],sum(r['question_semantic_score'] for r in rows)/20)
    assert math.isclose(s['answer_average'],sum(r['answer_similarity_score'] for r in pairs)/len(pairs))
    assert s['answer_above_70']==sum(r['answer_similarity_score']>=70 for r in pairs)
    root=Path(__file__).resolve().parents[1]
    for path,digest in protocol['service_hashes'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
    for name in ['translation-report.md','question-table.md','answer-table.md','details.md']:
        assert '\ufffd' not in (OUT/name).read_text(encoding='utf-8')
    for name in ['question-table.md','answer-table.md']:
        assert len((OUT/name).read_text(encoding='utf-8').splitlines())==22
    report={'passed':True,'count':20,'exact_original_references':True,'actual_api_pairs_verified':True,'metric_formulas_and_averages_verified':True,'production_hashes_unchanged':True}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__': main()

