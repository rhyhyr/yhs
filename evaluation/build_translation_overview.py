"""Build a compact overview and expandable per-question details from saved results."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'results' / 'translation_e2e'

def main():
    data = json.loads((OUT / 'results.json').read_text(encoding='utf-8'))
    rows, summary = data['rows'], data['summary']
    q, a = summary['questions'], summary['answers']
    topics = ['비자 연장 시기', '비자 연장 서류', '외국인등록증', '주소 변경 신고', '아르바이트 허가', '아르바이트 허가 서류', '주당 근로시간', '수강신청 기간', '수강신청 후 과목 추가', '휴학·복학', '유학생 장학금', '장학금 성적 기준', '등록금 납부 마감', '등록금 분할 납부', '국민건강보험 가입', '건강보험료 납부', '기숙사 신청', '기숙사 비용·납부 시기', '은행 계좌 개설', '졸업 학점']
    lines = ['# 번역 평가 결과 요약', '', f"**답변 번역 종합 점수: {a['average_translation_score']:.2f} / 100점 — 목표 80점 미달**", '', f"질문 번역: **{q['average_semantic_score']:.2f}점 — 목표 충족**. 영어 질문의 한국어 변환은 대체로 양호하지만, 한국어 답변을 영어로 전달할 때 정보 손실과 오역이 발생했습니다.", '', '| 평가 항목 | 평균 점수 / 100 | 80점 이상 | 목표 충족 |', '| --- | ---: | ---: | --- |', f"| 질문 번역 | {q['average_semantic_score']:.2f} | {q['above_80_count']}/20 (95%) | 충족 |", f"| 답변 번역 종합 | **{a['average_translation_score']:.2f}** | {a['above_80_count']}/20 (0%) | 미충족 |", f"| ↳ 의미 보존 | {a['average_semantic_preservation']:.2f} | — | — |", f"| ↳ 핵심정보 보존 | {a['average_critical_preservation']:.2f} | — | — |", '', '**점수 계산:** 질문 = BERTScore F1 × 100. 답변 종합 = 의미 보존 × 40% + 핵심정보 보존 × 60%. 질문과 답변을 합친 단일 점수는 사전에 정의하지 않았습니다.', '', '> 답변 점수는 고정 기준을 적용한 LLM 자동 평가 추정치입니다. 사람의 정확도 판정이나 COMET 점수가 아니며, 일부 오류 분류와 핵심정보 추출에는 검토가 필요합니다.', '', '## 20개 문항 점수', '', '모든 점수는 100점 만점입니다. 판정은 답변 종합 점수 80점을 기준으로 합니다.', '', '| ID | 질문 주제 | 질문 번역 | 답변 의미 | 핵심정보 | **답변 종합** | 판정 |', '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for row, topic in zip(rows, topics):
        score = row['answer_translation_score']
        lines.append(f"| {row['id']} | [{topic}](details.md#item-{row['id']}) | {row['question_semantic_score']:.2f} | {row['answer_semantic_preservation']:.2f} | {row['critical_information_preservation']:.2f} | **{score:.2f}** | {'통과' if score >= 80 else '미달'} |")
    lines += ['', '## 먼저 확인할 사례', '', '- **17번:** 질문 번역 88.35점, 답변 번역 28.00점. 질문 자체는 의미가 잘 보존됐지만, 답변에서 재학생을 졸업생으로 바꾸고 원화 금액을 달러로 표시하는 문제가 있습니다.', '- **18번:** 답변 종합 8.00점. 기숙사 금액을 학생 수로 번역하고 기간·기관명을 잘못 전달했습니다. 추출된 핵심정보 5개 기준이며, 답변의 모든 의미가 0% 보존됐다는 뜻은 아닙니다.', '- **19번:** 답변 종합 최고점 77.00점. 날짜는 보존됐지만 은행명과 대면·비대면 조건이 누락됐습니다.', '', '## 자동 평가에서 발견한 오류', '', '| 오류 유형 | 해당 답변 수 / 20 | 오류 건수 |', '| --- | ---: | ---: |']
    labels = {'Omission':'정보 누락', 'Addition':'정보 추가', 'Numeric Error':'숫자·금액 오류', 'Terminology Error':'용어 오역', 'Meaning Reversal':'의미 반전', 'Procedure Error':'절차 오류'}
    for key, value in summary['errors'].items():
        lines.append(f"| {labels[key]} | {value['affected_answer_count']} | {value['event_count']} |")
    lines += ['', '한 오류에 여러 유형이 붙을 수 있습니다. 자동 분류 건수이며 전문가가 확정한 오류 건수는 아닙니다.', '', '## 상세 자료', '', '- [문항별 전체 원문·번역·점수](details.md): 긴 답변은 표 대신 접어서 표시합니다.', '- [평가 방법과 분석을 포함한 전체 보고서](report.ko.md)', '- [질문 번역 원본 표](question-table.md) · [답변 번역 원본 표](answer-table.md)', '- [원본 결과 JSON](results.json) · [CSV](results.csv)', '']
    (OUT / 'overview.md').write_text('\n'.join(lines), encoding='utf-8')
    details = ['# 문항별 번역 상세', '', '[핵심 점수 요약으로 돌아가기](overview.md)', '']
    for row, topic in zip(rows, topics):
        details += [f'<a id="item-{row["id"]}"></a>', '', f'## {row["id"]}. {topic}', '', f"**질문 번역 {row['question_semantic_score']:.2f}점 · 답변 종합 {row['answer_translation_score']:.2f}점**", '', f"- 영어 질문: {row['english_question']}", f"- 기준 한국어: {row['reference']}", f"- 실제 한국어: {row['system_translation']}", '', '<details>', '<summary>한국어 답변 원문과 실제 영어 답변 펼치기</summary>', '', '### 한국어 답변 원문', '', row['korean_source_answer'], '', '### 실제 영어 답변', '', row['english_final_answer'], '', '</details>', '', f"답변 의미 보존: {row['answer_semantic_preservation']:.2f}점 · 핵심정보 보존: {row['critical_information_preservation']:.2f}점 ({row['critical_preserved_count']}/{row['critical_total_count']})", '', '[요약으로 돌아가기](overview.md)', '']
    (OUT / 'details.md').write_text('\n'.join(details), encoding='utf-8')
    assert len(rows) == len(topics) == 20
    for name in ['overview.md', 'details.md']:
        assert '\ufffd' not in (OUT / name).read_text(encoding='utf-8')
    print('Created overview.md and details.md; validated 20 items. Source scores unchanged.')

if __name__ == '__main__':
    main()
