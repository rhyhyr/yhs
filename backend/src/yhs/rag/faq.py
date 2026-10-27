"""
yhs/rag/faq.py

역할:
- 즉답 가능한 단순 질문에만 응답하는 FAQ 빠른 경로.
- 복합 질문·조건부 질문·비교 질문은 검색기로 넘긴다.
- 키워드 기반 매칭 → 일치하는 FAQ가 없으면 None 반환.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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



# 질문 커버리지 계산 시 "설명된" 것으로 치는 일반어·질문틀 토큰 (+ 조사).
# 이 외의 토큰이 매칭 키워드로 설명되지 않으면 질문에 FAQ 밖 내용이 있다는 뜻이다.
# ponytail: 고정 목록 휴리스틱. 형태소 분석기가 들어오면 그걸로 내용어만 세도록 바꿀 것.
_GENERIC_TOKENS = {"유학생", "외국인", "어떤", "뭐", "뭐야", "무엇", "있어", "있나요", "대상", "종류", "알려줘", "궁금해"}
_PARTICLES = ("", "도", "은", "는", "이", "가", "을", "를", "의", "이야", "야", "요", "이에요", "인가요")
_TOKEN_RE = re.compile(r"[^\s?!.,~]+")

# 즉답 최소 커버리지. experiments/faq_route_snapshot.py 측정 기준:
# 정상 즉답(in_db 정의형) = 1.00, 오답(cross_hop/dirty/시점의존) ≤ 0.50.
MIN_COVERAGE = 0.75


@dataclass
class FaqMatch:
    """FAQ 매칭 신뢰도 신호. confidence < MIN_COVERAGE 이면 즉답하지 않는다."""

    confidence: float = 0.0
    score: int = 0          # 1위 엔트리의 일치 키워드 수
    margin: int = 0         # 1위 - 2위 일치 키워드 수 (0 이면 애매 → 거부)
    coverage: float = 0.0   # 매칭 키워드(+일반어)로 설명되는 질문 토큰 비율
    entry_index: int | None = None
    reason: str = "keyword_miss"


def _is_generic(token: str) -> bool:
    return any(token == g + p for g in _GENERIC_TOKENS for p in _PARTICLES)


def _coverage(q_lower: str, keywords: list[str]) -> float:
    covered: set[int] = set()
    for kw in keywords:
        for m in re.finditer(re.escape(kw.lower()), q_lower):
            covered.update(range(m.start(), m.end()))
    tokens = list(_TOKEN_RE.finditer(q_lower))
    if not tokens:
        return 0.0
    ok = sum(1 for t in tokens if covered.intersection(range(t.start(), t.end())) or _is_generic(t.group()))
    return ok / len(tokens)


class FastPathHandler:
    """FAQ 키워드 매칭 기반 빠른 응답 처리기."""

    def match(self, question: str) -> str | None:
        """단순 즉답 가능한 질문에 FAQ 답변을 반환한다. 복합 질문이거나 신뢰도 미달이면 None."""
        answer, _ = self.match_with_score(question)
        return answer

    def match_with_score(self, question: str) -> tuple[str | None, FaqMatch]:
        """FAQ 답변과 신뢰도 신호를 함께 반환한다. 신뢰도 미달이면 답변은 None."""
        q_lower = question.lower().strip()

        # 복합/시간의존 질문은 정적 FAQ로 답할 수 없음 → 검색으로 넘김
        if _is_complex_question(q_lower):
            return None, FaqMatch(reason="complex_gate")

        hits = [[kw for kw in keywords if kw.lower() in q_lower] for keywords, _ in _FAQ_DB]
        ranked = sorted(range(len(hits)), key=lambda i: len(hits[i]), reverse=True)
        best = ranked[0]
        score = len(hits[best])
        if score == 0:
            return None, FaqMatch()

        m = FaqMatch(
            score=score,
            margin=score - (len(hits[ranked[1]]) if len(ranked) > 1 else 0),
            coverage=round(_coverage(q_lower, hits[best]), 3),
            entry_index=best,
        )
        if m.margin == 0:
            m.reason = "ambiguous_margin"
        elif m.coverage < MIN_COVERAGE:
            m.reason = "low_coverage"
        else:
            m.confidence, m.reason = m.coverage, "ok"
            return _FAQ_DB[best][1], m
        return None, m
