"""
yhs/rag/faq.py

역할:
- 즉답 가능한 단순 질문에만 응답하는 FAQ 빠른 경로.
- 복합 질문·조건부 질문·비교 질문은 검색기로 넘긴다.
- 키워드 기반 매칭 → 일치하는 FAQ가 없으면 None 반환.
"""

from __future__ import annotations

from yhs.core.settings import load_config

# ── 설정 ─────────────────────────────────────────────────────────────────────
# FAQ 문안과 복합질문 지시어는 backend/config/faq.yaml 에 있다.
# 운영 중 문안을 고칠 때 코드 배포 없이 YAML 만 바꾸면 된다.
_cfg = load_config("faq")

# 복합 질문 지시어: 이 패턴이 하나라도 있으면 FAQ를 건너뛰고 검색기로 넘긴다
_COMPLEX_INDICATORS: list[str] = list(_cfg["complex_indicators"])

# FAQ 템플릿: (키워드 목록, 답변)
_FAQ_DB: list[tuple[list[str], str]] = [
    (list(e["keywords"]), e["answer"]) for e in _cfg["entries"]
]


def _is_complex_question(question: str) -> bool:
    """복합·조건부·비교 질문이면 True를 반환한다."""
    q = question.lower()
    return any(ind in q for ind in _COMPLEX_INDICATORS)



class FastPathHandler:
    """FAQ 키워드 매칭 기반 빠른 응답 처리기."""

    def match(self, question: str) -> str | None:
        """단순 즉답 가능한 질문에 FAQ 답변을 반환한다. 복합 질문이거나 일치 없으면 None."""
        answer, _ = self.match_with_score(question)
        return answer

    def match_with_score(self, question: str) -> tuple[str | None, int]:
        """FAQ 답변과 키워드 매칭 점수(일치 키워드 수)를 함께 반환한다."""
        q_lower = question.lower().strip()

        # 복합/시간의존 질문은 정적 FAQ로 답할 수 없음 → 검색으로 넘김
        if _is_complex_question(q_lower):
            return None, 0

        best_answer: str | None = None
        best_match_count = 0

        for keywords, answer in _FAQ_DB:
            count = sum(1 for kw in keywords if kw.lower() in q_lower)
            if count > best_match_count:
                best_match_count = count
                best_answer = answer

        if best_match_count >= 1:
            return best_answer, best_match_count

        return None, 0
