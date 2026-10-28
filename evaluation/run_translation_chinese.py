"""Chinese live evaluation using the original service; same current metrics as English."""
import os, sys, json, inspect, hashlib, logging
from pathlib import Path
from datetime import datetime, timezone
import run_translation_e2e as base
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/results/translation_e2e_zh'
QUESTIONS=json.loads(r'''["\u6211\u4ec0\u4e48\u65f6\u5019\u53ef\u4ee5\u7533\u8bf7\u5ef6\u957f\u7b7e\u8bc1\uff1f","\u5ef6\u957f\u7b7e\u8bc1\u9700\u8981\u54ea\u4e9b\u6750\u6599\uff1f","\u5982\u4f55\u7533\u8bf7\u5916\u56fd\u4eba\u767b\u5f55\u8bc1\uff1f","\u5982\u679c\u6211\u7684\u4f4f\u5740\u53d8\u66f4\u4e86\uff0c\u9700\u8981\u7533\u62a5\u5417\uff1f","\u7559\u5b66\u751f\u505a\u517c\u804c\u9700\u8981\u83b7\u5f97\u8bb8\u53ef\u5417\uff1f","\u7533\u8bf7\u517c\u804c\u5de5\u4f5c\u8bb8\u53ef\u9700\u8981\u54ea\u4e9b\u6750\u6599\uff1f","\u7559\u5b66\u751f\u6bcf\u5468\u6700\u591a\u53ef\u4ee5\u505a\u591a\u5c11\u5c0f\u65f6\u7684\u517c\u804c\uff1f","\u9009\u8bfe\u65f6\u95f4\u662f\u4ec0\u4e48\u65f6\u5019\uff1f","\u9009\u8bfe\u7ed3\u675f\u540e\u8fd8\u53ef\u4ee5\u52a0\u9009\u8bfe\u7a0b\u5417\uff1f","\u5982\u4f55\u7533\u8bf7\u4f11\u5b66\u6216\u590d\u5b66\uff1f","\u7559\u5b66\u751f\u53ef\u4ee5\u7533\u8bf7\u54ea\u4e9b\u5956\u5b66\u91d1\uff1f","\u7533\u8bf7\u5956\u5b66\u91d1\u9700\u8981\u8fbe\u5230\u591a\u5c11\u5e73\u5747\u7ee9\u70b9\uff08GPA\uff09\uff1f","\u5b66\u8d39\u7f34\u7eb3\u7684\u622a\u6b62\u65e5\u671f\u662f\u4ec0\u4e48\u65f6\u5019\uff1f","\u5b66\u8d39\u53ef\u4ee5\u5206\u671f\u7f34\u7eb3\u5417\uff1f","\u5916\u56fd\u7559\u5b66\u751f\u4e5f\u5fc5\u987b\u53c2\u52a0\u97e9\u56fd\u56fd\u6c11\u5065\u5eb7\u4fdd\u9669\u5417\uff1f","\u5982\u4f55\u7f34\u7eb3\u5065\u5eb7\u4fdd\u9669\u8d39\uff1f","\u5982\u4f55\u7533\u8bf7\u5bbf\u820d\uff1f","\u5bbf\u820d\u8d39\u662f\u591a\u5c11\uff0c\u4ec0\u4e48\u65f6\u5019\u9700\u8981\u7f34\u7eb3\uff1f","\u5728\u97e9\u56fd\u5f00\u8bbe\u94f6\u884c\u8d26\u6237\u9700\u8981\u54ea\u4e9b\u6750\u6599\uff1f","\u6bd5\u4e1a\u9700\u8981\u4fee\u6ee1\u591a\u5c11\u5b66\u5206\uff1f"]''')
DATA=[(zh,pair[1]) for zh,pair in zip(QUESTIONS,base.DATA)]
def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
    os.environ['NEO4J_URI']='bolt://10.3.129.54:7687'
    import torch, numpy as np, random
    torch.set_num_threads(4); torch.manual_seed(42); np.random.seed(42); random.seed(42)
    OUT.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.WARNING,handlers=[logging.FileHandler(OUT/'execution.log',encoding='utf-8')])
    base.OUT=OUT; base.DATA=DATA
    from yhs.core.settings import get_settings
    settings=get_settings()
    protocol={'version':'Chinese-current-metrics-1','question_formula':'BERTScore F1 * 100','answer_formula':'cross-language BERTScore F1 * 100','model':'bert-base-multilingual-cased','layer':9,'idf':False,'baseline_rescaling':False,'question_threshold':80,'answer_display_threshold':70,'dataset':[{'id':i,'chinese_question':zh,'reference':ko} for i,(zh,ko) in enumerate(DATA,1)],'dataset_origin':'Simplified Chinese counterparts composed before testing; Korean references unchanged from supplied English dataset. Not independently native-speaker validated.','dataset_sha256':hashlib.sha256(json.dumps(DATA,ensure_ascii=False).encode()).hexdigest(),'service_hashes':base.hashes(),'runtime':{'profile_languages':['zh'],'translation_model':settings.translation_model,'answer_model':settings.openai_runtime_model,'transport':'real FastAPI TestClient /api/chat; production lifespan','neo4j_uri_override':'evaluation process only'},'limitations':'Korean-Chinese direct BERTScore is exploratory similarity, not calibrated translation accuracy.'}
    if (OUT/'protocol.json').exists():
        saved=base.read('protocol.json')
        assert saved['dataset_sha256']==protocol['dataset_sha256']
        assert saved['service_hashes']==base.hashes()
    else:
        protocol['frozen_utc']=datetime.now(timezone.utc).isoformat()
        base.write('protocol.json',protocol)
    # Reuse the exact observation/endpoint code with language and artifact labels adapted.
    source=inspect.getsource(base.collect).replace("'languages':['en']","'languages':['zh']").replace("'english_question'","'chinese_question'").replace("'english_final_answer'","'chinese_final_answer'").replace("'english_translation'","'chinese_translation'")
    exec(compile(source,'<Chinese evaluation collection>','exec'),base.__dict__)
    base.collect(os.environ['NEO4J_URI'])
    base.question_scores()
    rows=base.read('question-results.json')
    from bert_score import BERTScorer
    scorer=BERTScorer(model_type='bert-base-multilingual-cased',num_layers=9,lang='ko',device='cpu',batch_size=2,idf=False,rescale_with_baseline=False,use_fast_tokenizer=False)
    pairs=[r for r in rows if r.get('korean_source_answer')]
    if pairs:
        p,rec,f=scorer.score([r['chinese_final_answer'] for r in pairs],[r['korean_source_answer'] for r in pairs])
        for r,pv,rv,fv in zip(pairs,p.tolist(),rec.tolist(),f.tolist()):
            r.update(answer_precision=pv,answer_recall=rv,answer_f1=fv,answer_similarity_score=fv*100)
            r['answer_token_lengths']={key:len(scorer._tokenizer.encode(r[field],truncation=False)) for key,field in [('source','korean_source_answer'),('target','chinese_final_answer')]}
    for r in rows:
        if not r.get('korean_source_answer'):
            r.update(answer_similarity_score=None,answer_evaluation_status='N/A: no Korean translation source')
    summary={'total_count':20,'question_average':sum(r['question_semantic_score'] for r in rows)/20,'question_average_bleu':sum(r['smoothed_bleu'] for r in rows)/20,'question_above_80':sum(r['question_semantic_score']>=80 for r in rows),'answer_evaluated_count':len(pairs),'answer_average':sum(r['answer_similarity_score'] for r in pairs)/len(pairs) if pairs else None,'answer_above_70':sum(r['answer_similarity_score']>=70 for r in pairs),'translation_warning_count':sum(bool(r['translation_warnings']) for r in rows),'answer_over_token_limit_ids':[r['id'] for r in pairs if max(r['answer_token_lengths'].values())>512]}
    assert base.hashes()==base.read('protocol.json')['service_hashes']
    base.write('results.json',{'protocol':base.read('protocol.json'),'summary':summary,'rows':rows,'bertscore_hash':scorer.hash})
    from build_chinese_translation_report import render
    render()
    assert len(rows)==20 and all(r['status']=='ok' for r in rows)
    base.write('verification.json',{'passed':True,'total_count':20,'production_hashes_unchanged':True,'exact_references_preserved':all(r['reference']==DATA[r['id']-1][1] for r in rows),'actual_api_answers_match':all(r['chinese_final_answer']==r['api_response']['answer'] for r in rows)})
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

