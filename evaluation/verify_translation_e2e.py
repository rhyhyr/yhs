"""Check the real-run artifacts, exact pairing, frozen metrics and audit arithmetic."""
import hashlib
import importlib.metadata as metadata
import json
import math
from pathlib import Path
from statistics import mean
from sacrebleu.metrics import BLEU
from run_translation_e2e import DATA,hashes,validate_extraction,validate_judgment
from translation_protocol import PROTOCOL,ERROR_TYPES

OUT=Path(__file__).resolve().parent/'results/translation_e2e'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def close(a,b): assert math.isclose(a,b,abs_tol=1e-8),(a,b)
def main():
    data=read('results.json');rows=data['rows'];protocol=data['protocol'];summary=data['summary']
    assert len(rows)==20 and [r['id'] for r in rows]==list(range(1,21))
    assert [(r['english_question'],r['reference']) for r in rows]==DATA
    assert protocol['evaluation']==PROTOCOL
    assert protocol['dataset_sha256']=='96cbfcd0c667b45376b8302f94c93e4a18ebb93d6da31af2a613874c5a049a99'
    assert hashlib.sha256(json.dumps(DATA,ensure_ascii=False).encode()).hexdigest()==protocol['dataset_sha256']
    assert hashes()==protocol['service_hashes'],'Production files changed'
    collection=read('collection.json')
    assert len(collection)==20 and all(r['status']=='ok' for r in collection)
    raw={r['id']:r for r in collection}
    metric=BLEU(tokenize='char',smooth_method='exp',effective_order=True)
    evaluated=[]
    for row in rows:
        original=raw[row['id']]
        for k in ['system_translation','korean_source_answer','english_final_answer','api_response','translation_events','llm_events','retrieval_events']:
            assert row[k]==original[k]
        assert row['english_final_answer']==row['api_response']['answer']
        close(row['smoothed_bleu'],metric.sentence_score(row['system_translation'],[row['reference']]).score)
        close(row['question_semantic_score'],100*row['bertscore'])
        if row.get('answer_translation_score') is None:
            assert not row['korean_source_answer'] or row['answer_evaluation_status']=='no_critical_items'
            continue
        evaluated.append(row)
        events=row['translation_events']; assert events
        assert events[-1]['korean_source']==row['korean_source_answer']
        assert events[-1]['english_translation']==row['english_final_answer']
        if row['source_kind']=='llm': assert row['llm_events'][-1]['korean_internal_answer']==row['korean_source_answer']
        source=read(f"critical-source-{row['id']:02d}.json")
        assert source['translation_not_provided'] is True
        assert source['source_sha256']==hashlib.sha256(row['korean_source_answer'].encode()).hexdigest()
        validate_extraction({'items':source['items']},row['korean_source_answer'])
        matches=[read(p.name) for p in sorted(OUT.glob(f"judge-{row['id']:02d}-judge-*.json"))]
        valid=[x for x in matches if x['validation']=='passed']
        assert valid
        judged=json.loads(valid[-1]['raw_response'])
        validate_judgment(judged,row['korean_source_answer'],row['english_final_answer'],source['items'])
        assert len(row['critical_items'])==len(source['items'])
        assert [{k:a[k] for k in ['id','status','translation_quote','reason']} for a in row['critical_items']]==judged['items']
        assert [{k:a[k] for k in ['id','type','source_quote','fact']} for a in row['critical_items']]==source['items']
        n=sum(x['status']=='preserved' for x in row['critical_items'])
        assert row['critical_preserved_count']==n and row['critical_total_count']==len(source['items'])
        close(row['critical_information_preservation'],100*n/len(source['items']))
        close(row['answer_semantic_preservation'],judged['semantic_score'])
        close(row['answer_translation_score'],0.4*judged['semantic_score']+0.6*100*n/len(source['items']))
        assert row['translation_errors']==judged['errors']
        assert row['error_flags']=={t:any(t in e['types'] for e in judged['errors']) for t in ERROR_TYPES}
    q=summary['questions'];a=summary['answers']
    for summary_key,row_key in [('average_smoothed_bleu','smoothed_bleu'),('average_bertscore','bertscore'),('average_semantic_score','question_semantic_score')]:
        close(q[summary_key],mean(r[row_key] for r in rows))
    assert q['above_80_count']==sum(r['question_semantic_score']>=80 for r in rows)
    close(q['above_80_ratio'],q['above_80_count']/20)
    assert a['evaluated_count']==len(evaluated)
    if evaluated:
        for summary_key,row_key in [('average_semantic_preservation','answer_semantic_preservation'),('average_critical_preservation','critical_information_preservation'),('average_translation_score','answer_translation_score')]:
            close(a[summary_key],mean(r[row_key] for r in evaluated))
    assert a['above_80_count']==sum(r['answer_translation_score']>=80 for r in evaluated)
    for kind in ERROR_TYPES:
        assert summary['errors'][kind]['event_count']==sum(kind in e['types'] for r in rows for e in (r.get('translation_errors') or []))
        assert summary['errors'][kind]['affected_answer_count']==sum(r.get('error_flags',{}).get(kind,False) for r in rows)
    result={'status':'passed','question_count':20,'paired_answer_count':len(evaluated),
      'checks':['unchanged service hashes','exact supplied references','real API final output pairing','BLEU recomputation','question metric formula','source-only critical facts and exact evidence','raw live judge responses match stored scores','critical denominators and preservation counts','fixed answer weights','average/pass/error counts'],
      'post_install_versions':{p:metadata.version(p) for p in ['google-genai','openai','fastapi','httpx','torch','transformers','sacrebleu','bert-score']}}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
