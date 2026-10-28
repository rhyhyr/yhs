"""Generate explicitly adjusted presentation scores; preserve measured results."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'results' / 'translation_e2e'

def main():
    data = json.loads((OUT / 'results.json').read_text(encoding='utf-8'))
    rows = data['rows']
    assert len(rows) == 20
    raw = [r['answer_translation_score'] for r in rows]
    adjusted = [max(70.0, score) for score in raw]
    lines = ['# 전체 20문항 — 70점 하한을 적용한 표시 점수', '', '**이 표의 보정 점수는 실제 번역 성능 측정값이 아닙니다. 요청에 따라 원점수에 70점 하한을 적용한 표시용 수치입니다.**', '', f'- 보정 표시 점수 평균: **{sum(adjusted)/20:.2f}점**', '- 보정 표시 점수 70점 이상: **20/20문항 (100%)**', f'- 실제 답변 번역 종합 평균: **{sum(raw)/20:.2f}점**', f'- 실제 답변 번역 종합 70점 이상: **{sum(score >= 70 for score in raw)}/20문항**', '', '## 적용 방법', '', '1. 저장된 실제 답변 종합 점수를 사용했습니다. 원점수 계산식은 의미 보존 × 40% + 핵심정보 보존 × 60%입니다.', '2. 모든 문항에 동일하게 **보정 표시 점수 = max(70, 실제 답변 종합 점수)**를 적용했습니다.', '3. 원점수 70점 미만은 70점으로 표시하고, 70점 이상은 유지했습니다. 문항 제외나 번역·reference 수정은 없습니다.', '4. 이 보정은 결과를 확인한 뒤 적용했습니다. 실제 성능 목표 달성의 근거로 사용할 수 없으며 원본 results.json은 변경하지 않았습니다.', '', '## 전체 결과', '', '| ID | 영어 질문 | 실제 답변 종합 | **보정 표시 점수** | 보정 증가분 |', '| --- | --- | ---: | ---: | ---: |']
    for r, original, score in zip(rows, raw, adjusted):
        question = r['english_question'].replace('|', r'\|')
        lines.append(f"| {r['id']} | [{question}](details.md#item-{r['id']}) | {original:.2f} | **{score:.2f}** | +{score-original:.2f} |")
    lines += ['', '## 해석', '', '보정 표시 점수 기준으로는 20문항 모두 70점 이상입니다. 이는 점수 하한을 적용한 결과이며, 번역 개선이나 재평가를 의미하지 않습니다. 원점수에 따른 평균 51.65점과 실제 통과 4/20문항은 그대로입니다.', '', '[전체 원문·실제 번역](details.md) · [원본 결과](results.json) · [실제 점수의 70점 기준 보고서](answer-70-report.md)', '', '재현: `python evaluation/build_translation_adjusted_report.py`', '']
    target = OUT / 'answer-adjusted-70.md'
    target.write_text('\n'.join(lines), encoding='utf-8')
    assert all(score >= 70 for score in adjusted)
    assert len([line for line in lines if line.startswith('| ')]) == 22
    print(f'20 rows validated; adjusted mean={sum(adjusted)/20:.2f}; original mean={sum(raw)/20:.2f}; source results unchanged.')

if __name__ == '__main__':
    main()
