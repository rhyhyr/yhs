"""Present every saved answer score against a 70-point threshold."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'results' / 'translation_e2e'

def main():
    data = json.loads((OUT / 'results.json').read_text(encoding='utf-8'))
    rows = data['rows']
    assessed = [r for r in rows if r['answer_translation_score'] is not None]
    passed = sum(r['answer_translation_score'] >= 70 for r in assessed)
    average = sum(r['answer_translation_score'] for r in assessed) / len(assessed)
    lines = ['# 전체 20문항 답변 번역 평가 — 70점 기준', '', f'**평균 {average:.2f}점 / 100점 · 70점 이상 {passed}/20문항 ({passed / 20 * 100:.0f}%) · 전체 문항 70점 이상 목표 미충족**', '', '이 보고서는 저장된 실제 테스트 결과를 70점 기준으로 다시 표시합니다. 번역을 개선하거나 테스트를 재실행한 결과가 아닙니다. 종전 목표는 80점이며, 이번 보고서의 통과 기준만 요청에 따라 70점으로 표시했습니다.', '', '## 평가 방법', '', '- 평가 대상: 제공된 영어 질문 20개에 대해 실제 서비스가 생성한 한국어 답변과 최종 영어 답변.', '- 의미 보존: 고정된 이중언어 LLM 평가 기준에 따른 0~100점 추정치.', '- 핵심정보 보존: 한국어 원문에서 추출한 핵심정보 중 영어 답변에 보존된 항목 수 / 전체 추출 항목 수 × 100.', '- **답변 종합 점수 = 의미 보존 × 0.4 + 핵심정보 보존 × 0.6.**', '- 통과: 반올림 전 답변 종합 점수 ≥ 70. 정확히 70점은 통과에 포함합니다.', '- 20문항 모두 포함하며, 낮은 점수의 문항 제거·reference 변경·점수 하한 부여·결과를 본 뒤 가중치 조정은 하지 않았습니다.', '', '> 점수는 LLM 자동 평가 추정치이며 사람의 정확도 백분율이 아닙니다. 핵심정보 추출과 오류 분류에는 전문가 검토가 필요합니다. 일부 자동 판정의 한계는 기존 전체 보고서에 기록돼 있습니다.', '', '## 전체 결과', '', '| ID | 영어 질문 | 의미 보존 | 핵심정보 보존 | 보존 항목 | **답변 종합** | 70점 기준 |', '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        score = r['answer_translation_score']
        question = r['english_question'].replace('|', r'\|')
        lines.append(f"| {r['id']} | [{question}](details.md#item-{r['id']}) | {r['answer_semantic_preservation']:.2f} | {r['critical_information_preservation']:.2f} | {r['critical_preserved_count']}/{r['critical_total_count']} | **{score:.2f}** | {'통과' if score >= 70 else '미달'} |")
    lines += ['', '## 모든 문항에 70점 이상을 부여하지 않은 이유', '', '실제 점수를 확인한 뒤 문항을 선택하거나 점수 계산식을 조정하면, 70점 달성을 입증하는 독립적인 평가가 되지 않습니다. 모든 점수에 최저 70점을 부여하는 방식도 번역 품질을 측정하지 못합니다. 따라서 그런 방식으로 만든 수치를 실제 성능으로 제시하지 않았습니다.', '', '## 실제 성능 개선이 필요한 부분', '', '- 숫자·금액·통화 단위 보존: 3만원을 $30,000으로, 기숙사비를 학생 수로 바꾸는 오류를 막아야 합니다.', '- 행정 용어 보존: 재학생·휴학·복학·국제교류처·출입국관리사무소·TOPIK 등 용어를 일관되게 번역해야 합니다.', '- 답변 전체 정보 보존: 서류 목록, 연락처, 은행명, 신청 조건이 번역 과정에서 누락되지 않도록 확인해야 합니다.', '- 개선 후에는 동일한 20문항, reference, 계산식으로 실제 서비스를 다시 실행하고 이전 결과와 비교해야 합니다. 이번 작업에서는 서비스 수정이나 재평가를 수행하지 않았습니다.', '', '## 파일과 재현 방법', '', '- [문항별 한국어 원문과 실제 영어 답변](details.md)', '- [기존 평가 방법·오류 분석 전체 보고서](report.ko.md)', '- [실제 저장 결과](results.json)', '- 보고서 생성: `python evaluation/build_translation_70_report.py`', '']
    assert len(rows) == 20
    target = OUT / 'answer-70-report.md'
    target.write_text('\n'.join(lines), encoding='utf-8')
    assert len([line for line in lines if line.startswith('| ')]) == 22
    assert '\ufffd' not in target.read_text(encoding='utf-8')
    print(f'Validated all 20 rows; average={average:.2f}; >=70={passed}/20; original results unchanged.')

if __name__ == '__main__':
    main()
