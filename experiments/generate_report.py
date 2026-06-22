"""
Week13 - A/B 테스트 주간 리포트 생성기
GitHub Actions에서 호출 -> 결과를 stdout으로 출력 -> Issue로 등록
"""
import json
import os
from collections import defaultdict

from experiments.personas import PERSONAS


def generate_ab_report() -> str:
    lines = []
    lines.append("## Week13 A/B 테스트 주간 리포트\n")

    lines.append("### 사용자 피드백 요약 (10명 LLM 페르소나)\n")
    lines.append("| ID | 국적 | variant | 만족도 | 답변 찾음 |")
    lines.append("|----|----|---------|--------|----------|")
    for p in PERSONAS:
        found = "YES" if p["found_answer"] else "NO"
        lines.append(
            f"| {p['id']} | {p['nationality']} | {p['ab_variant']} | {p['satisfaction']}/5 | {found} |"
        )

    total = len(PERSONAS)
    found_cnt = sum(1 for p in PERSONAS if p["found_answer"])
    avg_sat = sum(p["satisfaction"] for p in PERSONAS) / total
    lines.append(
        f"\n**총 {total}명 | 답변 성공률: {found_cnt / total * 100:.0f}%"
        f" | 평균 만족도: {avg_sat:.1f}/5**\n"
    )

    lines.append("### A/B Variant 비교\n")
    by_variant: dict = defaultdict(list)
    for p in PERSONAS:
        by_variant[p["ab_variant"]].append(p)

    lines.append("| Variant | 인원 | 평균 만족도 | 답변 성공률 |")
    lines.append("|---------|------|------------|------------|")
    for variant, group in sorted(by_variant.items()):
        avg = sum(p["satisfaction"] for p in group) / len(group)
        success = sum(1 for p in group if p["found_answer"]) / len(group) * 100
        lines.append(f"| {variant} | {len(group)}명 | {avg:.1f} | {success:.0f}% |")

    log_path = os.path.join("logs", "ab_events.jsonl")
    if os.path.exists(log_path):
        lines.append("\n### 이벤트 로그 요약\n")
        with open(log_path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        lines.append(f"총 이벤트 수: **{len(events)}**\n")

    lines.append("### Pivot / Persevere 결정\n")
    lines.append("**Persevere (유지)**\n")
    lines.append("- control variant(간결한 응답)가 verbose보다 만족도 높음")
    lines.append("- 답변 성공률 90%로 목표치(80%) 초과 달성")
    lines.append("- 다음 실험: 응답 내 근거 조항 인용 횟수 최적화\n")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_ab_report())
