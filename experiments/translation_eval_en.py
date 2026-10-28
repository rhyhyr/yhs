"""Evaluate the unchanged production EN->KO translator on fixed references.
Run from repository root: python experiments/translation_eval_en.py
Never substitute translations; failed production fallbacks are retained.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'src'))
DATA = [
('When can I apply for a visa extension?', '비자 연장은 언제부터 신청할 수 있나요?'),
('What documents do I need to extend my visa?', '비자 연장을 위해 어떤 서류가 필요한가요?'),
('How can I apply for an Alien Registration Card?', '외국인등록증은 어떻게 신청하나요?'),
('Do I need to report it if I change my address?', '주소가 변경되면 신고해야 하나요?'),
('Do international students need permission to work part-time?', '유학생이 아르바이트를 하려면 허가를 받아야 하나요?'),
('What documents do I need to apply for a part-time work permit?', '아르바이트 허가를 신청하려면 어떤 서류가 필요한가요?'),
('How many hours can international students work per week?', '유학생은 일주일에 몇 시간까지 아르바이트할 수 있나요?'),
('When is the course registration period?', '수강신청 기간은 언제인가요?'),
('Can I add a course after the registration period is over?', '수강신청 기간이 끝난 후에도 과목을 추가할 수 있나요?'),
('How can I apply for a leave of absence or return to school?', '휴학이나 복학은 어떻게 신청하나요?'),
('What scholarships are available for international students?', '유학생이 신청할 수 있는 장학금에는 어떤 것이 있나요?'),
('What GPA do I need to apply for a scholarship?', '장학금을 신청하려면 어느 정도의 성적이 필요한가요?'),
('When is the tuition payment deadline?', '등록금 납부 마감일은 언제인가요?'),
('Can I pay my tuition in installments?', '등록금을 분할해서 납부할 수 있나요?'),
('Do international students have to enroll in Korean National Health Insurance?', '외국인 유학생도 국민건강보험에 가입해야 하나요?'),
('How can I pay my health insurance fee?', '건강보험료는 어떻게 납부하나요?'),
('How can I apply for a dormitory?', '기숙사는 어떻게 신청하나요?'),
('How much is the dormitory fee, and when do I have to pay it?', '기숙사비는 얼마이며 언제 납부해야 하나요?'),
('What documents do I need to open a bank account in Korea?', '한국에서 은행 계좌를 개설하려면 어떤 서류가 필요한가요?'),
('How many credits do I need to graduate?', '졸업하려면 몇 학점이 필요한가요?'),
]
BERT_MODEL = 'bert-base-multilingual-cased'
FORMULA = '0.5 * sentence_BLEU_0_to_100 + 0.5 * BERTScore_F1 * 100'

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

class Warnings(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []
    def emit(self, record):
        self.messages.append(record.getMessage())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'experiments/results/translation_en')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    import torch
    from sacrebleu.metrics import BLEU
    from bert_score import BERTScorer
    from yhs.core.settings import get_settings
    from yhs.rag.retrieval.translator import get_translator, is_translation_enabled, resolve_response_language
    torch.manual_seed(42)
    torch.set_num_threads(4)
    settings = get_settings()
    bleu = BLEU(tokenize='char', smooth_method='exp', effective_order=True)
    protocol = {
        'dataset': [{'id': i, 'english_question': en, 'reference': ko} for i,(en,ko) in enumerate(DATA,1)],
        'dataset_sha256': hashlib.sha256(json.dumps(DATA, ensure_ascii=False).encode()).hexdigest(),
        'formula': FORMULA, 'threshold': 80, 'weights': {'BLEU': 0.5, 'BERTScore': 0.5},
        'bleu': {'order': 4, 'tokenize': 'char', 'smooth_method': 'exp', 'effective_order': True},
        'bertscore': {'model': BERT_MODEL, 'num_layers': 9, 'idf': False, 'rescale_with_baseline': False, 'use_fast_tokenizer': False, 'batch_size': 4, 'device': 'cpu'},
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'translation_model': settings.translation_model,
        'translation_enabled': is_translation_enabled(),
        'translation_function': 'get_translator().translate_if_needed(question)',
        'profile_languages': ['en'], 'runtime_llm': settings.runtime_llm,
        'runtime_llm_used_for_translation': False,
        'python': platform.python_version(), 'platform': platform.platform(),
        'versions': {p: importlib.metadata.version(p) for p in ['torch','transformers','sacrebleu','bert-score','sentencepiece','langdetect']},
        'service_file_sha256': hashlib.sha256((ROOT/'backend/src/yhs/rag/retrieval/translator.py').read_bytes()).hexdigest(),
    }
    # Freeze dataset and protocol BEFORE any production translations are observed.
    dump(out/'protocol.json', protocol)
    capture = Warnings()
    logger = logging.getLogger('yhs.rag.retrieval.translator')
    logger.addHandler(capture)
    translator = get_translator()
    rows = []
    for i,(en,ko) in enumerate(DATA,1):
        capture.messages.clear()
        detected = translator.detect_language(en)
        start = time.perf_counter()
        actual, translated = translator.translate_if_needed(en) if is_translation_enabled() else (en,False)
        row = {'id': i, 'english_question': en, 'reference': ko, 'system_translation': actual,
               'detected_language': detected, 'was_translated': translated,
               'response_language': resolve_response_language(en,['en']),
               'translation_seconds': time.perf_counter()-start, 'warnings': list(capture.messages),
               'bleu': bleu.sentence_score(actual,[ko]).score}
        rows.append(row)
        dump(out/'translations.json', rows)
        print(f'{i}/20 {actual}', flush=True)
    print('Computing BERTScore with fixed protocol...', flush=True)
    scorer = BERTScorer(model_type=BERT_MODEL, num_layers=9, lang='ko', device='cpu',
                        batch_size=4, idf=False, rescale_with_baseline=False, use_fast_tokenizer=False)
    precision, recall, f1 = scorer.score([r['system_translation'] for r in rows],[r['reference'] for r in rows])
    for r,p,rec,f in zip(rows,precision.tolist(),recall.tolist(),f1.tolist()):
        r.update(bertscore=f, bertscore_precision=p, bertscore_recall=rec,
                 final_score=0.5*r['bleu']+50*f)
        if not all(math.isfinite(r[k]) for k in ['bleu','bertscore','final_score']):
            raise ValueError('Nonfinite score')
    summary = {'count':len(rows), 'average_bleu':mean(r['bleu'] for r in rows),
               'average_bertscore':mean(r['bertscore'] for r in rows),
               'average_final_score':mean(r['final_score'] for r in rows),
               'above_80_count':sum(r['final_score']>=80 for r in rows),
               'translation_fallback_count':sum(not r['was_translated'] for r in rows),
               'translation_warning_count':sum(bool(r['warnings']) for r in rows),
               'bert_score_hash':scorer.hash, 'bleu_signature':str(bleu.get_signature()),
               'translation_model_commit':getattr(getattr(translator._model,'config',None),'_commit_hash',None),
               'bertscore_model_commit':getattr(scorer._model.config,'_commit_hash',None)}
    summary['above_80_ratio'] = summary['above_80_count']/len(rows)
    summary['meets_average_80'] = summary['average_final_score']>=80
    summary['meets_80_percent_item_rate'] = summary['above_80_ratio']>=0.8
    dump(out/'results.json', {'protocol':protocol,'summary':summary,'rows':rows})
    with (out/'results.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines=['| ID | English Question | Reference | System Translation | BLEU | BERTScore | Final Score |',
           '| -- | ---------------- | --------- | ------------------ | ---- | --------- | ----------- |']
    for r in rows:
        cells=[str(r['id']),r['english_question'],r['reference'],r['system_translation'],f"{r['bleu']:.2f}",f"{r['bertscore']:.4f}",f"{r['final_score']:.2f}"]
        lines.append('| '+' | '.join(c.replace('|',r'\|').replace('\n',' ') for c in cells)+' |')
    (out/'table.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
