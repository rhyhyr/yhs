"""Live /api/chat evaluation. No production algorithms or outputs are replaced.
python evaluation/run_translation_e2e.py --phase collect --neo4j-uri bolt://HOST:7687
python evaluation/run_translation_e2e.py --phase questions
python evaluation/run_translation_e2e.py --phase answers
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata as metadata
import json
import logging
import math
import os
import random
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend/src'),str(ROOT/'experiments')]
from translation_eval_en import DATA
from translation_protocol import PROTOCOL, QUESTION_MODEL, JUDGE_MODEL, EXTRACT_PROMPT, JUDGE_PROMPT, ERROR_TYPES, CRITICAL_TYPES
OUT=ROOT/'evaluation/results/translation_e2e'
SERVICE_PATHS=['backend/src/yhs/api/service.py','backend/src/yhs/api/deps.py','backend/src/yhs/api/routes/chat.py','backend/src/yhs/rag/engine.py','backend/src/yhs/rag/retrieval/translator.py','backend/src/yhs/rag/retrieval/linker.py','backend/src/yhs/rag/retrieval/vector_retriever.py','backend/src/yhs/rag/llm/openai_client.py','backend/config/retrieval.yaml','backend/config/runtime.yaml','backend/config/crawler.yaml','backend/config/faq.yaml']

def hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SERVICE_PATHS if (ROOT/p).exists()}
def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/name
    temp=target.with_suffix(target.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(target)
def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))
def initialize_protocol(uri=None):
    path=OUT/'protocol.json'
    if path.exists():
        frozen=read('protocol.json')
        assert frozen['service_hashes']==hashes(),'Production files changed since protocol was frozen'
        assert frozen['evaluation']==PROTOCOL,'Evaluation protocol changed'
        return
    from yhs.core.settings import get_settings
    s=get_settings()
    versions={}
    for p in ['torch','transformers','sentence-transformers','sacrebleu','bert-score','openai','neo4j','fastapi','httpx','huggingface-hub']:
        try: versions[p]=metadata.version(p)
        except metadata.PackageNotFoundError: versions[p]=None
    write('protocol.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),
        'evaluation':PROTOCOL,'service_hashes':hashes(),'versions':versions,
        'dataset':[{'id':i,'english_question':en,'reference':ko} for i,(en,ko) in enumerate(DATA,1)],
        'dataset_sha256':hashlib.sha256(json.dumps(DATA,ensure_ascii=False).encode()).hexdigest(),
        'runtime':{'translation_model':s.translation_model,'translation_enabled':s.enable_zh_translation,
          'embedding_model':s.embedding_model,'llm_provider':s.runtime_llm,'answer_model':s.openai_runtime_model,
          'original_neo4j_uri':s.neo4j_uri,'effective_neo4j_uri':uri or s.neo4j_uri,
          'uri_override_scope':'evaluation process only; .env unchanged','profile_languages':['en'],
          'generation':'unchanged service settings','transport':'FastAPI TestClient real POST /api/chat and lifespan',
          'test_date_seoul':'2026-10-08'},'python':sys.version,'seed':42})

@contextmanager
def observe(obj,name,callback):
    original=getattr(obj,name)
    def observed(*args,**kwargs):
        result=original(*args,**kwargs)
        callback(args,kwargs,result)
        return result
    setattr(obj,name,observed)
    try: yield
    finally: setattr(obj,name,original)

class TranslationWarnings(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages=[]
    def emit(self,record): self.messages.append(record.getMessage())

def collect(uri, rerun_ids=None):
    from fastapi.testclient import TestClient
    from yhs.api.main import create_app
    from yhs.api import service
    from yhs.rag.retrieval.translator import get_translator,is_translation_enabled
    rows=read('collection.json') if (OUT/'collection.json').exists() else []
    if rerun_ids:
        write('collection-before-environment-retry.json', rows)
        rows=[r for r in rows if r['id'] not in rerun_ids]
        write('collection.json', rows)
    done={r['id'] for r in rows if r['status']=='ok'}
    capture=TranslationWarnings()
    logging.getLogger('yhs.rag.retrieval.translator').addHandler(capture)
    with TestClient(create_app(),raise_server_exceptions=True) as client:
        state=client.app.state.resources
        assert state.store.verify_connectivity(),'Neo4j unreachable'
        db_counts=state.store._run('MATCH (n) RETURN labels(n) AS labels, count(n) AS count')
        write('database-before.json',db_counts)
        for i,(en,ko) in enumerate(DATA,1):
            if i in done: continue
            rows=[r for r in rows if r['id']!=i]
            start=time.perf_counter()
            capture.messages.clear()
            translator=get_translator()
            actual,translated=translator.translate_if_needed(en) if is_translation_enabled() else (en,False)
            translation_events=[]; retrieval_events=[]; llm_events=[]
            def record_translation(a,k,result):
                translation_events.append({'korean_source':a[0],'target_language':a[1] if len(a)>1 else k['language'],'english_translation':result})
            def record_retrieval(a,k,result):
                retrieval_events.append({'question':a[0],'method':result.retrieval_method,
                    'chunk_count':len(result.chunks),'chunk_ids':[c.id for c in result.chunks]})
            def record_llm(a,k,result):
                llm_events.append({'question':a[0],'korean_internal_answer':result,
                    'context_sha256':hashlib.sha256(a[1].encode()).hexdigest()})
            try:
                with observe(service,'_to_response_language',record_translation),observe(state.engine,'retrieve',record_retrieval),observe(state.llm,'generate_answer',record_llm):
                    response=client.post('/api/chat',json={'channelId':'translation-evaluation','message':en,'history':[],'languages':['en']})
                    response.raise_for_status()
                    payload=response.json()
                pair=translation_events[-1] if translation_events else None
                source=pair['korean_source'] if pair else None
                if pair: assert pair['english_translation']==payload['answer']
                stage='llm' if llm_events else ('faq' if not retrieval_events and pair else ('retrieval_context' if pair else 'direct_response_no_translation'))
                row={'id':i,'english_question':en,'reference':ko,'system_translation':actual,
                    'was_translated':translated,'detected_language':translator.detect_language(en),
                    'status':'ok','source_kind':stage,'korean_source_answer':source,
                    'english_final_answer':payload['answer'],'api_response':payload,
                    'translation_events':translation_events,'retrieval_events':retrieval_events,'llm_events':llm_events,
                    'translation_warnings':list(capture.messages),'elapsed_seconds':time.perf_counter()-start,
                    'collected_utc':datetime.now(timezone.utc).isoformat(),
                    'numeric_source_spans':re.findall(r'\d+(?:[.,:/-]\d+)*',source or ''),
                    'numeric_translation_spans':re.findall(r'\d+(?:[.,:/-]\d+)*',payload['answer'])}
                if source and translator._tokenizer:
                    row['source_line_token_lengths']=[len(translator._tokenizer(line)['input_ids']) for line in source.splitlines() if line.strip()]
                rows.append(row)
                rows.sort(key=lambda r:r['id'])
                write('collection.json',rows)
                print(f"{i}/20 source={stage}, ko={len(source or '')} chars, en={len(payload['answer'])} chars, {row['elapsed_seconds']:.1f}s",flush=True)
            except Exception as exc:
                rows.append({'id':i,'english_question':en,'reference':ko,'system_translation':actual,'status':'error','error_type':type(exc).__name__,'error':str(exc),'elapsed_seconds':time.perf_counter()-start})
                write('collection.json',rows)
                raise
        write('database-after.json',state.store._run('MATCH (n) RETURN labels(n) AS labels, count(n) AS count'))
    assert len(rows)==20 and all(r['status']=='ok' for r in rows)
    assert hashes()==read('protocol.json')['service_hashes']
    print('Live endpoint collection complete: 20/20',flush=True)

def question_scores():
    from sacrebleu.metrics import BLEU
    from bert_score import BERTScorer
    rows=read('collection.json')
    assert len(rows)==20 and all(r['status']=='ok' for r in rows)
    bleu=BLEU(tokenize='char',smooth_method='exp',effective_order=True)
    scorer=BERTScorer(model_type=QUESTION_MODEL,num_layers=9,lang='ko',device='cpu',batch_size=4,idf=False,rescale_with_baseline=False,use_fast_tokenizer=False)
    p,r,f=scorer.score([x['system_translation'] for x in rows],[x['reference'] for x in rows])
    for row,pv,rv,fv in zip(rows,p.tolist(),r.tolist(),f.tolist()):
        row.update(smoothed_bleu=bleu.sentence_score(row['system_translation'],[row['reference']]).score,
                   bertscore=fv,bertscore_precision=pv,bertscore_recall=rv,question_semantic_score=100*fv)
    write('question-results.json',rows)
    write('question-metric-metadata.json',{'bertscore_hash':scorer.hash,'bleu_signature':str(bleu.get_signature()),'bert_model_commit':getattr(scorer._model.config,'_commit_hash',None)})
    print('Question scoring complete',flush=True)

def request_json(client,system,payload,validator,stage,i):
    last=None
    for attempt in range(1,4):
        messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
        if last is not None:
            messages.append({'role':'user','content':f'Previous response violated validation: {last}. Correct the schema/evidence and follow the ORIGINAL rules. Do not adjust a score to pass any threshold.'})
        response=client.chat.completions.create(model=JUDGE_MODEL,temperature=0,seed=42,
            messages=messages,
            response_format={'type':'json_object'},max_tokens=6500)
        raw=response.choices[0].message.content or ''
        evidence={'id':i,'stage':stage,'attempt':attempt,'model':response.model,'request_id':response.id,
                  'system_fingerprint':response.system_fingerprint,'usage':response.usage.model_dump() if response.usage else None,'raw_response':raw}
        try:
            result=json.loads(raw)
            validator(result)
            evidence['validation']='passed'
            write(f'judge-{i:02d}-{stage}-{attempt}.json',evidence)
            return result
        except (ValueError,AssertionError,KeyError,TypeError) as exc:
            last=exc
            evidence.update(validation='failed',error=str(exc))
            write(f'judge-{i:02d}-{stage}-{attempt}.json',evidence)
    raise ValueError(f'Judge output failed evidence/schema validation for item {i}: {last}')

def validate_extraction(value,source):
    items=value['items']; assert isinstance(items,list)
    assert [x['id'] for x in items]==list(range(1,len(items)+1))
    for item in items:
        assert item['type'] in CRITICAL_TYPES
        assert isinstance(item['source_quote'],str) and item['source_quote'] and item['source_quote'] in source
        assert isinstance(item['fact'],str) and item['fact']
        quote=item['source_quote']
        if '.pdf' in quote.lower():
            spans=[m.span() for m in re.finditer(r'\[[^\]\n]*\.pdf[^\]\n]*\]', source, flags=re.I)]
            marker=re.search(r'(?m)^\s*(?:\[출처\]|출처\s*:)',source)
            if marker: spans.append((marker.start(),len(source)))
            positions=[m.start() for m in re.finditer(re.escape(quote),source)]
            only_citation=positions and all(any(start<=pos and pos+len(quote)<=end for start,end in spans) for pos in positions)
            assert not only_citation, f'Item {item["id"]} is a pure source citation filename, excluded by the ORIGINAL extraction protocol; remove it and renumber remaining substantive facts'

def validate_judgment(value,source,target,items):
    score=value['semantic_score']; assert isinstance(score,(float,int)) and not isinstance(score,bool)
    assert math.isfinite(score) and 0<=score<=100
    assert isinstance(value['semantic_reason'],str) and value['semantic_reason']
    assert [x['id'] for x in value['items']]==[x['id'] for x in items]
    for item in value['items']:
        assert item['status'] in ['preserved','omitted','mistranslated','uncertain']
        quote=item['translation_quote']; assert isinstance(quote,str)
        assert not quote or quote in target
        if item['status']=='preserved': assert quote
        assert isinstance(item['reason'],str) and item['reason']
    assert isinstance(value['errors'],list)
    for error in value['errors']:
        assert error['types'] and set(error['types']).issubset(ERROR_TYPES)
        assert isinstance(error['source_quote'],str) and (not error['source_quote'] or error['source_quote'] in source)
        assert isinstance(error['translation_quote'],str) and (not error['translation_quote'] or error['translation_quote'] in target)
        assert error['description']

def audit_pair(client, row):
    i=row['id']; source=row['korean_source_answer']; target=row['english_final_answer']
    cache_name=f'ready-audit-{i:02d}.json'
    source_hash=hashlib.sha256(source.encode()).hexdigest()
    target_hash=hashlib.sha256(target.encode()).hexdigest()
    if (OUT/cache_name).exists():
        cached=read(cache_name)
        assert cached['source_sha256']==source_hash and cached['translation_sha256']==target_hash
        validate_extraction({'items':cached['items']},source)
        validate_judgment(cached['judgment'],source,target,cached['items'])
        return cached['items'],cached['judgment']
    source_file=OUT/f'critical-source-{i:02d}.json'
    if source_file.exists():
        extracted=read(source_file.name)
        assert extracted['source_sha256']==source_hash
        items=extracted['items']; validate_extraction({'items':items},source)
    else:
        value=request_json(client,EXTRACT_PROMPT,{'korean_source':source},lambda v:validate_extraction(v,source),'extract',i)
        items=value['items']
        write(source_file.name,{'source_sha256':source_hash,'items':items,'translation_not_provided':True})
    judged=request_json(client,JUDGE_PROMPT,{'korean_source':source,'english_translation':target,'source_critical_items':items},lambda v:validate_judgment(v,source,target,items),'judge',i)
    write(cache_name,{'source_sha256':source_hash,'translation_sha256':target_hash,'items':items,'judgment':judged})
    return items,judged

def audit_ready():
    from openai import OpenAI
    from yhs.core.settings import get_settings
    client=OpenAI(api_key=get_settings().openai_api_key,timeout=120,max_retries=2)
    for row in read('collection.json'):
        if row['status']!='ok' or not row.get('korean_source_answer'): continue
        audit_pair(client,row)
        print(f"Prepared real answer audit: ID {row['id']}",flush=True)
    client.close()

def answer_scores():
    from openai import OpenAI
    from yhs.core.settings import get_settings
    client=OpenAI(api_key=get_settings().openai_api_key,timeout=120,max_retries=2)
    rows=read('question-results.json')
    scored=read('answer-results.json') if (OUT/'answer-results.json').exists() else []
    done={r['id'] for r in scored}
    for row in rows:
        i=row['id']
        if i in done: continue
        source=row['korean_source_answer']; target=row['english_final_answer']
        if not source or not re.search('[가-힣]',source):
            row.update(answer_semantic_preservation=None,critical_information_preservation=None,
                       answer_translation_score=None,answer_evaluation_status='not_applicable_no_korean_translation_pair',
                       critical_items=[],translation_errors=None)
        else:
            items,judged=audit_pair(client,row)
            audits=[dict(original,**review) for original,review in zip(items,judged['items'])]
            count=sum(x['status']=='preserved' for x in audits)
            critical=100*count/len(items) if items else None
            semantic=float(judged['semantic_score'])
            total=0.4*semantic+0.6*critical if critical is not None else None
            row.update(answer_semantic_preservation=semantic,critical_information_preservation=critical,
                       answer_translation_score=total,answer_evaluation_status='evaluated' if items else 'no_critical_items',
                       critical_items=audits,critical_preserved_count=count,critical_total_count=len(items),
                       semantic_reason=judged['semantic_reason'],translation_errors=judged['errors'],
                       error_flags={t:any(t in e['types'] for e in judged['errors']) for t in ERROR_TYPES})
        scored.append(row); scored.sort(key=lambda r:r['id']);write('answer-results.json',scored)
        print(f"{i}/20 semantic={row['answer_semantic_preservation']} critical={row['critical_information_preservation']} total={row['answer_translation_score']}",flush=True)
    client.close()
    summarize(scored)

def summarize(rows):
    def avg(key):
        vals=[r[key] for r in rows if r.get(key) is not None]
        return mean(vals) if vals else None
    qpass=sum(r['question_semantic_score']>=80 for r in rows)
    evaluated=[r for r in rows if r.get('answer_translation_score') is not None]
    apass=sum(r['answer_translation_score']>=80 for r in evaluated)
    qmean=avg('question_semantic_score'); amean=avg('answer_translation_score')
    summary={'total_count':len(rows),
      'questions':{'average_smoothed_bleu':avg('smoothed_bleu'),'average_bertscore':avg('bertscore'),
        'average_semantic_score':qmean,'above_80_count':qpass,'above_80_ratio':qpass/len(rows),
        'meets_target':len(rows)==20 and qmean>=80},
      'answers':{'average_semantic_preservation':avg('answer_semantic_preservation'),
        'average_critical_preservation':avg('critical_information_preservation'),
        'average_translation_score':amean,'evaluated_count':len(evaluated),
        'not_applicable_count':len(rows)-len(evaluated),'above_80_count':apass,
        'above_80_ratio_evaluated':apass/len(evaluated) if evaluated else None,
        'above_80_ratio_all_20':apass/len(rows),
        'meets_target_evaluated':amean>=80 if amean is not None else None,
        'meets_target_all_20':amean>=80 if len(evaluated)==20 else None},
      'errors':{t:{'affected_answer_count':sum(r.get('error_flags',{}).get(t,False) for r in rows),
          'event_count':sum(t in e['types'] for r in rows for e in (r.get('translation_errors') or []))} for t in ERROR_TYPES},
      'source_kinds':{kind:sum(r['source_kind']==kind for r in rows) for kind in sorted({r['source_kind'] for r in rows})},
      'translation_warning_item_count':sum(bool(r.get('translation_warnings')) for r in rows),
      'question_translation_fallback_count':sum(not r['was_translated'] for r in rows),
      'source_lines_over_512_item_count':sum(any(n>512 for n in r.get('source_line_token_lengths',[])) for r in rows)}
    write('summary.json',summary)
    write('results.json',{'protocol':read('protocol.json'),'summary':summary,'rows':rows})
    with (OUT/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        columns=['id','english_question','reference','system_translation','smoothed_bleu','bertscore','question_semantic_score','source_kind','korean_source_answer','english_final_answer','answer_semantic_preservation','critical_information_preservation','answer_translation_score','answer_evaluation_status','translation_errors','critical_items']
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        writer.writerows({k:json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else r.get(k) for k in columns} for r in rows)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['collect','questions','answers','audit-ready','all'],default='all')
    parser.add_argument('--neo4j-uri')
    parser.add_argument('--rerun-ids', help='Comma-separated IDs to rerun after an environment repair; previous collection is archived')
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args(); OUT=args.output
    OUT.mkdir(parents=True, exist_ok=True)
    logging.getLogger().addHandler(logging.FileHandler(OUT/'execution.log', encoding='utf-8'))
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
    if args.neo4j_uri: os.environ['NEO4J_URI']=args.neo4j_uri
    import numpy as np
    import torch
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
    initialize_protocol(args.neo4j_uri)
    if args.phase in ['collect','all']: collect(args.neo4j_uri, {int(x) for x in args.rerun_ids.split(',')} if args.rerun_ids else None)
    if args.phase=='audit-ready': audit_ready()
    if args.phase in ['questions','all']: question_scores()
    if args.phase in ['answers','all']: answer_scores()
    assert hashes()==read('protocol.json')['service_hashes']

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.WARNING)
    main()
