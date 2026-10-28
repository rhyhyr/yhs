"""Render the 19-section Korean report from actual persisted evaluation results."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/results/translation_e2e'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def fmt(value,n=2): return 'N/A' if value is None else f'{value:.{n}f}'
def cell(value,limit=None):
    s='N/A' if value is None else str(value)
    if limit and len(s)>limit: s=s[:limit]+'…'
    return s.replace('|',r'\|').replace('\n','<br>')
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(cell(x) for x in row)+' |' for row in rows])

def main():
    data=read('results.json'); rows=data['rows']; summary=data['summary']; protocol=data['protocol']
    q=summary['questions']; a=summary['answers']
    top=max(rows,key=lambda r:r['question_semantic_score']); bottom=min(rows,key=lambda r:r['question_semantic_score'])
    assessed=[r for r in rows if r.get('answer_translation_score') is not None]
    sections=[]
    def section(number,title,text): sections.append(f'## {number}. {title}\n\n{text}')
    section(1,'평가 목적','실제 외국인 유학생의 영어 질문이 한국어 의미로 변환되는 품질과, 실제 서비스가 생성한 한국어 답변이 최종 영어 출력에서 보존되는 품질을 분리했다. 20개 영어 질문을 실제 FastAPI /api/chat 경로에 POST했다. 모델·검색·번역 출력을 수동 작성하거나 mock으로 대체하지 않았다. RAG 답변의 사실 정확성은 번역 평가와 별개다.')
    section(2,'현재 프로젝트의 다국어 처리 구조', '''실제 경로:

`frontend/src/api/chat.js sendMessage` → `backend/src/yhs/api/routes/chat.py chat()` → `service.answer_question()`.

- `resolve_response_language(question, ['en'])`이 최종 응답 언어를 영어로 정한다.
- FAQ는 영어 원문으로 `FastPathHandler.match()`한다. 일치 시 한국어 FAQ 문안을 `_to_response_language()`로 번역한다.
- 일반 검색은 `RetrievalEngine.retrieve(영어 원문)`를 호출한다. 내부 `EntityLinker._step0_llm_normalize()`에서 NLLB `translate_if_needed()`로 한국어를 만든다. 이 한국어는 엔티티 링킹/앵커에 사용된다.
- 벡터 검색·소스 라우팅·일부 재랭크에는 영어 원문이 전달된다. 따라서 모든 검색이 한국어 질문만 사용하는 직렬 구조는 아니다. Deep path에서는 영어 질의 확장·추가 검색·웹 검색을 수행할 수 있다.
- OpenAIRuntimeClient.generate_answer()는 영어 원문 질문과 검색 context를 받아 한국어 답변을 생성한다. `_SYSTEM_PROMPT` 규칙 7이 한국어로만 답하도록 한다. temperature=0, max_tokens=1024.
- `service._to_response_language()` → `QueryTranslator.translate_answer()`가 같은 한국어 답변을 줄 단위로 영어로 번역한다. NLLB는 `eng_Latn/kor_Hang` 언어 토큰을 사용하며 자연어 번역 prompt는 없다.
- `ChatResponse.answer`에 최종 영어 문자열을 반환한다.
- 근거가 부족한 no_answer 분기는 `insufficient_evidence_message('en')`을 직접 반환한다. 여기에는 번역 전 한국어 답변이 없으므로 답변 번역 점수를 N/A로 기록한다. 별도 한국어 질의를 재실행해 가짜 원문을 만들지 않는다.

수집은 관찰용 wrapper가 원래 함수를 그대로 실행하고 반환 문자열만 기록했다. `_to_response_language`가 받은 한국어 원문과 반환 영어가 실제 API 응답과 동일함을 검사했다. 서비스 코드와 번역 생성 설정은 변경하지 않았다.''')
    section(3,'평가 데이터셋','총 20문항, 영어 입력·한국어 질문 reference·영어 최종 응답. 비자/외국인등록/주소변경, 시간제 취업, 수강신청/휴복학/장학금/등록금/졸업, 건강보험, 기숙사, 금융 분야다. Korean Reference는 사용자가 제공한 문장을 그대로 사용했다. 데이터·지표·prompt·가중치는 최초 서비스 실행 전에 protocol.json에 저장했다. 데이터 SHA-256: '+protocol['dataset_sha256'])
    section(4,'Question Translation 평가 방식','BERTScore F1×100을 주 지표 Question Semantic Score로 사용했다. 의미가 같은 어순 변경·의역에 대한 BLEU의 과도한 감점을 피하기 위한 사용자 지정 방식이다. BERTScore는 다국어 BERT 9층 토큰 임베딩의 최대 코사인 유사도로 precision/recall 및 F1을 계산한다. IDF와 baseline rescaling은 적용하지 않았다. Smoothed BLEU는 보조 지표이며 합격 판정에 포함하지 않는다. SacreBLEU sentence BLEU-4, char tokenizer, exp smoothing, effective_order=True로 계산했다. 평균은 문항별 산술평균이다. BLEU의 문자 단위 설정과 BERTScore 모델은 기존 평가와 같고 종합식만 이번 요청대로 변경했다. 이전 보고서/결과는 덮어쓰지 않았다. 이 변화는 번역 시스템 개선이 아니라 평가 정의 변경이다. BERTScore 값은 인간 의미 정확도의 백분율로 검증된 값이 아니다.')
    section(5,'Answer Translation 평가 방식', '''정답 영어 reference를 작성하지 않았다. 실제 한국어 원문과 해당 원문의 실제 영어 출력을 직접 비교했다.

선호 reference-free QE 모델 `Unbabel/wmt22-cometkiwi-da`의 hparams.yaml 실제 접근 요청은 GatedRepoError/HTTP 401로 실패했다(qe-preflight.json). 모델 승인/인증이 없어 이 모델을 실행하지 못했다. `Unbabel/wmt20-comet-qe-da`는 공식 설명상 점수가 unbounded/noisy여서 사전 보정 근거 없이 0~100으로 바꾸지 않았다.

대안은 `gpt-4o`의 reference-free 이중언어 평가다. 전체 원문/번역을 읽고 고정 rubric으로 의미 보존을 평가한다: 100 의미 완전 보존, 90~99 사소한 비핵심 뉘앙스, 80~89 제한된 국소 의미 손실, 60~79 중요한 누락/오역 또는 여러 손실, 40~59 여러 중대한 오류, 20~39 큰 의미 손실, 0~19 대부분 무관/사용 불가. 자연스러운 표현 차이는 감점 근거로 삼지 않는다. 이 값은 COMET 점수나 객관적 확률이 아닌 LLM 평가 추정치다.

핵심정보는 별도 첫 요청에서 한국어 원문만 보고 추출한다. 영어 출력은 이 추출 요청에 제공하지 않는다. 날짜/기간/시간/숫자/금액/학점/서류/기관/장소/행정용어/신청조건/자격/허용·금지/의무·선택/절차/제한을 원자 사실로 기록한다. 서류 목록은 각 서류와 제출 의무를 분리한다. 중복 사실과 순수 Markdown/파일명·페이지 표시는 제외하며 원문의 정확한 인용문을 저장한다.

두 번째 요청에서 각 항목의 영어 보존 여부를 preserved/omitted/mistranslated/uncertain으로 판정한다. 원문/영어 evidence가 실제 문자열의 부분문자열인지 검증한다. uncertain은 보존으로 세지 않는다. 원문 사실이 0개면 N/A로 처리하고 100점을 부여하지 않는다.

`Critical Information Preservation = 보존 항목 수 / 전체 원문 핵심정보 수 ×100`

`Answer Translation Score = 의미 보존 ×0.4 + 핵심정보 보존 ×0.6`

행정 안내에서 숫자·서류·조건·의무 보존을 우선하므로 60%를 배정했다. 실행 전에 설명하고 전체 문항에 고정 적용했으며 결과를 보고 가중치를 바꾸지 않았다. 의미 점수는 전체 텍스트, 핵심정보 점수는 추출 항목을 대상으로 한다. 사람의 교차 검토 없이 확정적 품질 판정으로 해석해서는 안 된다.''')
    metric=read('question-metric-metadata.json')
    judge_models=sorted({read(p.name)['model'] for p in OUT.glob('judge-*-judge-*.json')})
    section(6,'사용한 평가 모델 및 라이브러리',table(['항목','값'],[
      ['번역',protocol['runtime']['translation_model']],['검색 임베딩',protocol['runtime']['embedding_model']],
      ['서비스 답변 LLM',protocol['runtime']['answer_model']],['웹 링크 선택 LLM','gpt-5.4-mini (실제 크롤 출력에서 확인)'],['BERTScore','bert-base-multilingual-cased / layer 9'],
      ['BERTScore hash',metric['bertscore_hash']],['BERT model commit',metric['bert_model_commit']],
      ['답변 평가 요청 모델','gpt-4o'],['실제 평가 API 응답 모델',', '.join(judge_models)],
      ['평가 seed/temperature/스레드','42 / 0 / CPU 4'],['API 실행','FastAPI TestClient, 실제 /api/chat, 실제 lifespan'],
      ['Python',protocol['python']],*[[p,v] for p,v in protocol['versions'].items()]])+'\n\nNEO4J_URI의 기존 잘못된 형식 '+protocol['runtime']['original_neo4j_uri']+' 대신 같은 서버의 확인된 '+protocol['runtime']['effective_neo4j_uri']+'를 평가 프로세스에만 적용했다. .env는 수정하지 않았다. .env를 dotenv로 프로세스에 로드해 기존 OpenAI 클라이언트의 환경변수 조회 방식과 맞췄다. 기존 서비스의 필수 패키지 누락(openai, fastapi, httpx, json-repair, google-genai)을 설치했다. 특히 ID 3 deep path에서 google-genai 누락이 발견되어 설치 후 이미 성공한 ID 1·2를 유지하고 중단 지점부터 재실행했다. 실제 원격 DB 조회/서비스 초기화에 성공했으며 모델 다운로드·계정 접근 문제는 숨기지 않았다. Playwright 1.55.0에 맞는 Chromium 1187이 없어 설치하고 deep-path ID 3, 4, 8, 9, 10을 재실행했다. 초기 전체 결과는 collection-before-environment-retry.json에 보관했다. 기존 크롤러의 Embedder.encode(show_progress_bar=False) 호출과 실제 encode 서명이 맞지 않아 캐시 저장이 실패하는 비치명적 경고 4건도 execution.log에 남겼다. 이 기존 서비스 결함은 평가 목적으로 수정하지 않았고, 원래 코드의 fallback을 사용했다.')
    qt=table(['ID','English Question','Korean Reference','System Korean Translation','Smoothed BLEU','BERTScore','Semantic Score'],[[r['id'],r['english_question'],r['reference'],r['system_translation'],fmt(r['smoothed_bleu']),fmt(r['bertscore'],4),fmt(r['question_semantic_score'])] for r in rows])
    (OUT/'question-table.md').write_text(qt+'\n',encoding='utf-8')
    section(7,'Question Translation 전체 결과 테이블',qt)
    at=table(['ID','Korean Source Answer','English Final Answer','Semantic Preservation','Information Preservation','Translation Error','Answer Translation Score'],[[r['id'],cell(r.get('korean_source_answer'),180),cell(r['english_final_answer'],230),fmt(r.get('answer_semantic_preservation')),fmt(r.get('critical_information_preservation')),', '.join(t for t,v in r.get('error_flags',{}).items() if v) or ('없음' if r.get('answer_evaluation_status')=='evaluated' else 'N/A'),fmt(r.get('answer_translation_score'))] for r in rows])
    (OUT/'answer-table.md').write_text(at+'\n',encoding='utf-8')
    section(8,'Answer Translation 전체 결과 테이블',at+'\n\n표의 긴 답변은 일부만 표시했다. 전체 한국어/영어 문자열·정보 항목·판정 근거·오류 인용은 results.json/results.csv에 저장했다. N/A는 0점이나 성공을 뜻하지 않으며 평가할 실제 한국어→영어 쌍이 없는 경우다.')
    section(9,'Question Translation 평균 결과',table(['지표','값'],[
      ['Average BERTScore',fmt(q['average_bertscore'],6)],['Average Question Semantic Score',fmt(q['average_semantic_score'],4)],
      ['Average Smoothed BLEU',fmt(q['average_smoothed_bleu'],4)],['80점 이상 문항 수',str(q['above_80_count'])+' / 20'],
      ['80점 이상 문항 비율',fmt(q['above_80_ratio']*100)+'%']]))
    section(10,'Answer Translation 평균 결과',table(['지표','값'],[
      ['실제 번역 쌍 평가 수',str(a['evaluated_count'])+' / 20'],['N/A 수',a['not_applicable_count']],
      ['Average Semantic Preservation',fmt(a['average_semantic_preservation'],4)],
      ['Average Critical Information Preservation',fmt(a['average_critical_preservation'],4)],
      ['Average Answer Translation Score',fmt(a['average_translation_score'],4)],
      ['80점 이상 문항 수',str(a['above_80_count'])+' / '+str(a['evaluated_count'])+' evaluated'],
      ['평가된 문항 중 비율',fmt(a['above_80_ratio_evaluated']*100 if a['above_80_ratio_evaluated'] is not None else None)+'%'],
      ['전체 20문항 기준 비율',fmt(a['above_80_ratio_all_20']*100)+'%']])+'\n\nN/A를 평균의 분모에 넣거나 100점으로 치환하지 않았다. 전체 20문항 중 일부가 N/A라면 평가 가능한 번역 쌍의 평균만 제시하며 전체 20문항 답변 번역 목표 충족 여부는 판정 불가로 남긴다.')
    section(11,'Translation Error 분석',table(['오류 유형','발생 사건 수','발생 답변 수'],[[t,x['event_count'],x['affected_answer_count']] for t,x in summary['errors'].items()])+'\n\n이 횟수는 LLM 자동 판정 결과이며 전문가가 확정한 실제 오류 횟수는 아니다. 각 사건은 여러 오류 유형에 해당할 수 있으므로 유형별 사건 수의 합이 고유 오류 사건 수와 같지 않을 수 있다. 질문 번역에서의 오류는 이 답변 오류 횟수에 섞지 않았다. 추가 근거 검토에서 ID 18의 문의 권고는 영어에도 존재하므로 해당 Omission 판정은 과검출 가능성이 있고, 원문에도 출처가 있어 해당 Addition 판정은 잘못된 출처 번역을 추가 오류로 분류한 가능성이 있다. ID 3의 여권 날인 오역은 반대 의미라기보다 용어/의미 왜곡에 가까워 Meaning Reversal 분류의 적합성도 추가 검토가 필요하다. 원시 자동 판정과 고정 점수는 수정하지 않고 이 제한을 함께 기록한다.\n\n'+ '\n\n'.join(f"- ID {r['id']}: "+' / '.join(e['description'] for e in (r.get('translation_errors') or [])) for r in rows if r.get('translation_errors')))
    answer_decision='충족' if a['meets_target_all_20'] is True else ('미충족' if a['meets_target_all_20'] is False else '전체 20문항 판정 불가: 일부 번역 쌍 N/A')
    section(12,'목표 기준 80점 충족 여부',f"질문: 평균 {fmt(q['average_semantic_score'])}점, {'충족' if q['meets_target'] else '미충족'}. 답변: 평가 가능한 쌍의 평균 {fmt(a['average_translation_score'])}점; {answer_decision}. 기준은 평균 ≥80이며 개별 통과율 80%와 다르다. 답변 점수는 대체 LLM 방법의 추정값으로 COMET 또는 사람의 검증된 정확도로 해석하지 않는다. 실제 미달 결과도 그대로 남겼다. 질문 점수와 답변 점수를 하나의 평균으로 합치지 않았다.")
    lowest=min(assessed,key=lambda r:r['answer_translation_score']) if assessed else None
    section(13,'낮은 점수가 나온 사례 분석',f"질문 최저는 ID {bottom['id']} ({fmt(bottom['question_semantic_score'])}점): {bottom['system_translation']}. 질문 최고는 ID {top['id']} ({fmt(top['question_semantic_score'])}점): {top['system_translation']}. ID 10의 휴학/복학, ID 12의 GPA→점수점, ID 13의 마감일→납부 가능 기간, ID 14의 분할 납부→할당처럼 핵심 용어·의미가 훼손된 출력은 별도로 해석해야 한다. BERTScore가 80점 이상이어도 이런 오류가 사라진 것은 아니다.\n\n"+(f"답변 최저는 ID {lowest['id']} ({fmt(lowest['answer_translation_score'])}점). {lowest.get('semantic_reason','')}" if lowest else '평가 가능한 답변 쌍이 없어 최저 답변 점수 사례를 만들지 않았다.'))
    r17=next(r for r in rows if r['id']==17)
    section(14,'BLEU와 의미 기반 평가가 다르게 나타난 사례',f"ID 17: reference '{r17['reference']}', 실제 '{r17['system_translation']}'. BLEU {fmt(r17['smoothed_bleu'])}, BERTScore {fmt(r17['bertscore'],4)}, Semantic Score {fmt(r17['question_semantic_score'])}. 기숙사 신청 방법이라는 의미는 보존됐고 어순/조사/정중 표현 차이 때문에 문자 n-gram 일치도가 낮다. 이번 정의에서는 BLEU를 합격 판정에 반영하지 않는다. 이를 시스템 번역이 개선됐다고 해석하거나 임의로 90점으로 올리지 않았다. 주소변경 신고(ID 4), 보험료 납부(ID 16)도 유사한 표현 차이가 있다.")
    best=min(assessed,key=lambda r:(-r['critical_information_preservation'],-r['answer_translation_score'])) if assessed else None
    section(15,'결론',f"실제 서비스 요청 수는 {len(rows)}/20이다. 질문 평균은 {fmt(q['average_semantic_score'])}점이며 답변 평균은 {fmt(a['average_translation_score'])}점(평가 가능 {a['evaluated_count']}/20)이다. 질문 의미 점수와 답변 번역 충실도를 분리했고 답변 factual correctness는 평가하지 않았다. "+(f"핵심정보 보존이 가장 높은 사례 중 하나는 ID {best['id']}: {best['critical_preserved_count']}/{best['critical_total_count']}항목 보존, {fmt(best['critical_information_preservation'])}점이다. " if best else '')+f"질문 원문 fallback {summary['question_translation_fallback_count']}건, 번역 warning 문항 {summary['translation_warning_item_count']}건, 512토큰을 넘는 원문 줄 문항 {summary['source_lines_over_512_item_count']}건이다. LLM 판정에 사람의 교차 검토가 없어 확정적 정확도 백분율로 주장하지 않는다. BERTScore·LLM judge는 행정 용어 오류를 놓치거나 과대평가할 수 있다. LLM 핵심정보 추출도 완전하지 않다. 예를 들어 ID 18에서 원문의 납부 시기 확인 불가라는 정보가 영어에 남아 있지만 추출된 5항목에는 포함되지 않았다. 따라서 그 문항의 정보 보존 0점은 추출한 5항목 기준의 자동 결과이며 모든 정보가 0% 보존됐다는 의미가 아니다. 이처럼 분모의 완전성과 오류 분류에는 전문가 검토가 필요하다.\n\n직접 확인한 오류 예: ID 3 사진 1매/3.5X4.5cm 조건 누락 및 3만원→$30,000 통화 오류; ID 13 복학→졸업과 차기 등록기간 누락; ID 15 문의처 안내 누락; ID 17 재학생→졸업생과 90만원→$900,000; ID 18 원화 비용→750,000/900,000 students; ID 19 은행 목록과 대면/비대면 사용 조건 누락. ID 19의 2025년 3월 21일은 March 21, 2025로 보존됐다. 이 사례는 실제 문자열을 비교한 번역 충실도 분석이며 안내 내용의 사실 정확성 검증은 아니다.")
    section(16,'성능 개선이 필요한 경우 개선 방법','NLLB의 외국인등록증·휴학/복학·GPA·납부 마감일·분할 납부 용어 처리 개선을 검토한다. 생성 답변의 긴 줄은 기존 512토큰 truncation으로 정보 손실 가능성이 있으므로 문장/토큰 단위 분할을 검토한다. 숫자·서류·조건·부정 표현의 보존 검사를 운영 번역 출력에 적용하는 방법을 검토한다. 검색은 실제 코드에서 한국어 엔티티 링킹과 영어 벡터/라우팅이 혼합되므로 검색 품질은 별도 실험으로 평가한다. 이번 작업에서는 이 개선을 서비스에 적용하지 않았다. 같은 데이터·설정으로 개선 전후를 비교하고 미사용 질문, 전문가 검토를 추가해야 한다. 이번에는 512토큰 초과 줄이 0건인데도 ID 15의 문의처 안내와 ID 19의 은행 목록/대면·비대면 조건이 누락됐다. 따라서 현재 누락을 단순 truncation 탓으로 단정하지 말고, 긴 여러 문장·목록의 번역 생성/EOS 종료와 문장 분할을 조사해야 한다. 기존 크롤러 임베딩 인자 불일치는 별도 서비스 수정 대상으로 남겼다.')
    section(17,'실행한 평가 코드 위치','''저장소 루트에서 실행:

```powershell
python evaluation/preflight_qe.py
python evaluation/run_translation_e2e.py --phase collect --neo4j-uri bolt://10.3.129.54:7687
python evaluation/run_translation_e2e.py --phase questions
python evaluation/run_translation_e2e.py --phase answers
python evaluation/build_translation_report.py
python evaluation/verify_translation_e2e.py
```

collect는 성공한 ID를 유지하고 중단 지점부터 재개한다. 최초 protocol을 고정하므로 코드/지표가 달라지면 같은 결과 폴더에서 실행을 중단한다. 새 실행에는 `--output`으로 새 폴더를 지정한다. 결과 점수나 출력이 바뀌는 경우 원인을 기록해야 한다. 모델 API의 seed와 temperature=0은 완전한 재현성을 보장하지 않아 요청 ID·실제 모델·system fingerprint·원시 평가 응답을 저장했다.''')
    section(18,'새로 생성하거나 수정한 파일','''새로 생성: evaluation/.gitignore, evaluation/requirements.txt, evaluation/translation_protocol.py, evaluation/run_translation_e2e.py, evaluation/preflight_qe.py, evaluation/build_translation_report.py, evaluation/verify_translation_e2e.py, evaluation/revalidate_source_facts.py, evaluation/README.md.

산출물: evaluation/results/translation_e2e/{protocol.json, qe-preflight.json, collection.json, question-results.json, question-metric-metadata.json, answer-results.json, summary.json, results.json, results.csv, question-table.md, answer-table.md, report.ko.md, verification.json, database-before.json, database-after.json}, 원문 전용 critical-source-XX.json, 모든 API 평가 원시 응답 judge-XX-{extract,judge}-attempt.json, 해시로 연결한 ready-audit-XX.json, execution.log, judge-model-preflight.json, collection-before-environment-retry.json, rejected-citation-audits/의 초기 제외 규칙 위반 응답과 manifest.json.

기존 서비스 코드·번역 로직·reference·이전 experiments 평가 결과·.env는 수정하지 않았다. 결과 디렉터리는 evaluation/.gitignore로 제외되므로 Git 커밋과 별도로 결과 파일을 보관해야 한다. 필수 패키지 설치는 로컬 Python 환경에 반영됐다.''')
    section(19,'구현 과정에서 명시되지 않아 임의로 결정한 사항','''1. 질문 BERTScore는 기존 실험과 같은 다국어 BERT 9층, IDF/baseline 보정 없음, slow tokenizer로 고정했다. 주 지표 식은 사용자 지정 F1×100을 따랐다.
2. 보조 BLEU는 char tokenization, exp smoothing, effective order, 문항별 평균을 선택했다.
3. 접근 불가한 COMETKiwi 대신 reference-free gpt-4o 평가를 실행했다. LLM 평가임을 명시하며 평가 모델의 정량적 인간 상관은 검증하지 않았다.
4. 행정 핵심정보의 중요성을 근거로 답변 의미 40%·핵심정보 60%를 사전 고정했다.
5. 핵심정보 추출을 한국어 원문만 보는 독립 요청으로 분리했다. 중복과 순수 메타데이터 제외, uncertain=미보존, 원문 항목 0개=N/A 규칙을 선택했다.
6. API TestClient의 실제 route/lifespan을 사용하고 원래 함수를 그대로 실행하는 관찰 wrapper로 번역 전후를 수집했다. 데이터나 모델 반환값을 mock으로 대체하지 않았다.
7. 잘못된 Neo4j URI는 확인된 같은 서버의 Bolt 주소로 평가 프로세스에서만 보완했다. .env와 서비스 코드는 유지했다.
8. source 없는 영어 직접 반환은 N/A로 처리하고 한국어 질문 재실행·역번역으로 원문을 만들지 않았다.
9. LLM 출력의 JSON 구조와 정확한 인용을 검증하고 실패 시 최대 3회 실제 요청을 재시도했다. 원시 응답과 실패 기록은 보관한다. 초기 6문항의 LLM 추출이 사전에 제외한 출처 PDF 파일명을 포함해 이 기존 규칙을 검증 코드에도 적용하고 위반 응답을 보관한 뒤 실제 재추출·재평가했다. 평가 기준·reference·가중치는 변경하지 않았다.
10. 오류는 고유 사건 목록과 유형별 발생 사건 수/영향 문항 수를 둘 다 기록했다. 하나의 사건이 여러 유형에 해당할 수 있다.
11. 표는 긴 답변을 일부 표시하고 전체 원문은 JSON/CSV에 저장했다. 원점수로 판정하고 표시에서만 반올림했다.
12. CPU 4스레드, random/numpy/torch/LLM seed 42를 사용했다. 모델 별칭의 변동성과 원격 DB 상태는 완전히 고정할 수 없다는 한계를 기록했다.

참고: [SacreBLEU](https://github.com/mjpost/sacrebleu), [BERTScore](https://github.com/Tiiiger/bert_score), [COMETKiwi 모델](https://huggingface.co/Unbabel/wmt22-cometkiwi-da), [기존 COMET-QE 점수 범위](https://huggingface.co/Unbabel/wmt20-comet-qe-da).''')
    (OUT/'report.ko.md').write_text('# 실제 서비스 다국어 번역 평가 — 2026-10-08\n\n'+'\n\n'.join(sections)+'\n',encoding='utf-8')
    print('Report and two full tables saved.')
if __name__=='__main__': main()
