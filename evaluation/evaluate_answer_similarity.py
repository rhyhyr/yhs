"""Supplementary cross-language token similarity; not calibrated translation accuracy."""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import hashlib
import json
from pathlib import Path
import torch
from bert_score import BERTScorer

OUT = Path(__file__).resolve().parent / 'results' / 'translation_e2e'

def main():
    source_path = OUT / 'results.json'
    original = source_path.read_bytes()
    data = json.loads(original)
    rows = data['rows']
    assert len(rows) == 20
    protocol = {'name':'Supplementary cross-language BERTScore', 'model':'bert-base-multilingual-cased', 'layer':9, 'idf':False, 'baseline_rescaling':False, 'formula':'BERTScore F1 * 100', 'threshold':70, 'source_sha256':hashlib.sha256(original).hexdigest(), 'limitations':['Direct Korean-English comparison is exploratory and not calibrated translation quality estimation.', 'Raw unscaled scores may be high even for weak matches.', 'Numeric and administrative terminology errors can be missed.', 'Long texts may be truncated by model token limit.'], 'metric_selection':'Post-hoc supplementary metric selected after original results; not an independent pass/fail validation.'}
    (OUT / 'answer-similarity-protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    torch.manual_seed(42)
    torch.set_num_threads(4)
    scorer = BERTScorer(model_type=protocol['model'],num_layers=9,lang='ko',device='cpu',batch_size=2,idf=False,rescale_with_baseline=False,use_fast_tokenizer=False)
    sources = [r['korean_source_answer'] for r in rows]
    targets = [r['english_final_answer'] for r in rows]
    precision, recall, f1 = scorer.score(targets,sources)
    results=[]
    for r,p,rec,f in zip(rows,precision.tolist(),recall.tolist(),f1.tolist()):
        lengths={key:len(scorer._tokenizer.encode(value,add_special_tokens=True,truncation=False)) for key,value in [('source',r['korean_source_answer']),('target',r['english_final_answer'])]}
        results.append({'id':r['id'],'english_question':r['english_question'],'precision':p,'recall':rec,'f1':f,'similarity_score':100*f,'original_answer_score':r['answer_translation_score'],'token_lengths':lengths})
    mean=sum(r['similarity_score'] for r in results)/20
    passed=sum(r['similarity_score']>=70 for r in results)
    report={'protocol':protocol,'bertscore_hash':scorer.hash,'average':mean,'above_70_count':passed,'rows':results}
    (OUT/'answer-similarity-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 답변 번역 추가 평가: 다국어 토큰 유사도','',f'**추가 유사도 평균: {mean:.2f}점 · 70점 이상: {passed}/20문항 ({passed*5}%)**','','실제 한국어 답변과 실제 최종 영어 답변을 다국어 BERT 임베딩으로 비교했습니다. 점수 하한이나 가산점은 적용하지 않았습니다. 서비스 재실행이나 번역 개선 없이 기존 실제 출력 20쌍을 다시 계산했습니다.','','## 평가 기준과 설계 이유','','- 평가식: **다국어 BERTScore F1 × 100**. 후보는 영어 답변, 비교 대상은 같은 요청의 한국어 원문입니다.','- 토큰 간 문맥 임베딩 코사인 유사도의 최대값을 이용해 precision과 recall을 계산하고 조화평균 F1을 구합니다.','- 표현·어순 차이를 완화하고 별도 핵심정보 추출의 판정 오류 영향을 없애는 보조 지표입니다.','- 모델: `bert-base-multilingual-cased`, 9층, CPU, IDF 미사용, baseline rescaling 미사용. 모든 문항에 같은 설정을 적용했습니다.','- 원시 BERTScore는 baseline 보정 점수보다 수치가 높게 나오는 경향이 있습니다. 이는 모델의 유사도 척도 특성이며 실제 정확도 백분율을 뜻하지 않습니다.','- 한국어와 영어를 직접 비교하는 이 사용법은 탐색적인 교차 언어 유사도 평가입니다. 일반적인 동일 언어 reference 비교와 다르며, 한영 번역 품질에 대한 검증된 합격 척도로 제시하지 않습니다.','- 기존 결과를 확인한 후 선택한 보조 지표이므로, 높은 점수를 독립적인 성능 검증으로 해석할 수 없습니다.','','## 전체 20문항 결과','','| ID | 영어 질문 | BERTScore P | BERTScore R | **추가 유사도 점수** | 70점 이상 | 기존 답변 점수 |','| --- | --- | ---: | ---: | ---: | --- | ---: |']
    for r in results:
        lines.append(f"| {r['id']} | [{r['english_question']}](details.md#item-{r['id']}) | {r['precision']:.4f} | {r['recall']:.4f} | **{r['similarity_score']:.2f}** | {'예' if r['similarity_score']>=70 else '아니오'} | {r['original_answer_score']:.2f} |")
    limit=scorer._tokenizer.model_max_length
    truncated=[r['id'] for r in results if max(r['token_lengths'].values())>limit]
    lines += ['', '## 해석과 한계','',f'모델 토큰 한도: {limit}. 한도를 초과한 문항: {truncated if truncated else "없음"}. 초과 시 문장 후반이 평가에서 제외될 수 있습니다.','', '숫자·통화·행정 용어 오류와 정보 누락을 이 점수 하나로 확인할 수 없습니다. 따라서 기존 실제 답변 평가 평균 51.65점을 대체하거나 서비스가 실제로 70% 정확하다고 주장하지 않습니다. 예컨대 기숙사 비용의 통화 단위가 틀려도 주변 문맥이 비슷하면 유사도는 높을 수 있습니다.','','## 근거와 재현','','- [BERTScore 공식 구현](https://github.com/Tiiiger/bert_score)','- [공식 baseline rescaling 설명](https://github.com/Tiiiger/bert_score/blob/master/journal/rescale_baseline.md)','- [실제 추가 계산 결과 JSON](answer-similarity-results.json)','- [전체 원문·번역](details.md)','- 실행: `python evaluation/evaluate_answer_similarity.py`','','원본 results.json과 서비스 코드는 변경하지 않았습니다.']
    (OUT/'answer-similarity-report.md').write_text('\n'.join(lines),encoding='utf-8')
    from build_translation_combined_report import render
    render()
    assert source_path.read_bytes()==original
    assert len(results)==20
    print(json.dumps({'average':mean,'above_70':passed,'token_limit':limit,'over_limit_ids':truncated,'original_unchanged':True}))

if __name__=='__main__':
    main()
