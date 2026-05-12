from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .crawler.web_search_client import WebSearchClient


class QuestionType(str, Enum):
    GENERAL = "general"
    COMPARISON = "comparison"
    CAUSE = "cause"
    EXCEPTION = "exception"
    DEADLINE = "deadline"
    DOCUMENTS = "documents"
    APPLICATION = "application"


@dataclass
class GateThresholds:
    min_top_score: float = 0.25
    min_evidence_chunks: int = 2

    @classmethod
    def from_env(cls) -> "GateThresholds":
        return cls(
            min_top_score=float(os.environ.get("GATE_MIN_TOP_SCORE", "0.25")),
            min_evidence_chunks=int(os.environ.get("GATE_MIN_EVIDENCE", "2")),
        )


# 텍스트에 한자/한글이 포함되어 있는지 정규식으로 판별해서 언어 코드를 반환한다.
# 한자+한글이 동시에 있으면 한국어(ko), 한자만 있으면 중국어(zh), 그 외 영어(en).
def detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        if re.search(r"[가-힣]", text):
            return "ko"
        return "zh"
    if re.search(r"[가-힣]", text):
        return "ko"
    return "en"


# 연속된 공백을 하나로 줄이고 앞뒤 공백을 제거한다.
# 검색 전 쿼리를 정규화하는 용도.
def normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# 키워드 매칭으로 질문 유형(QuestionType)을 판별한다.
# 비교/원인/예외/기한/서류/신청 순으로 체크하고 해당 없으면 GENERAL 반환.
# → 이 결과가 should_use_deep_path()에서 deep path 강제 여부 결정에 사용된다.
def detect_question_type(text: str) -> QuestionType:
    t = text.lower()

    if _contains_any(t, ["비교", "차이", "둘 중", "versus", "difference", "compare", "区别", "比较"]):
        return QuestionType.COMPARISON
    if _contains_any(t, ["왜", "원인", "이유", "cause", "reason", "why", "原因", "为什么"]):
        return QuestionType.CAUSE
    if _contains_any(t, ["예외", "제외", "except", "unless", "exception", "例外", "除外"]):
        return QuestionType.EXCEPTION
    if _contains_any(t, ["기한", "마감", "언제까지", "deadline", "due", "截至", "期限"]):
        return QuestionType.DEADLINE
    if _contains_any(t, ["서류", "준비물", "필요", "documents", "required", "材料", "文件"]):
        return QuestionType.DOCUMENTS
    if _contains_any(t, ["신청", "절차", "어떻게", "apply", "process", "流程", "办理"]):
        return QuestionType.APPLICATION
    return QuestionType.GENERAL


# 원본 쿼리에 '비교/원인/예외' 계열 키워드를 붙인 변형 쿼리 목록을 만든다.
# deep path에서 여러 각도로 검색할 때 사용한다. 중복은 제거한다.
def expand_query(text: str, language: Optional[str] = None) -> list[str]:
    lang = language or detect_language(text)
    base = normalize_query(text)
    variants = [base]

    if lang == "ko":
        variants.extend([
            f"{base} 비교 차이",
            f"{base} 원인 이유",
            f"{base} 예외 제외",
        ])
    elif lang == "zh":
        variants.extend([
            f"{base} 比较 区别",
            f"{base} 原因 为什么",
            f"{base} 例外 除外",
        ])
    else:
        variants.extend([
            f"{base} comparison difference",
            f"{base} cause reason",
            f"{base} exception unless",
        ])

    uniq: list[str] = []
    seen: set[str] = set()
    for v in variants:
        if v not in seen:
            uniq.append(v)
            seen.add(v)
    return uniq


# fast path 결과를 보고 deep path로 넘어가야 할지 판단한다.
# 아래 3가지 중 하나라도 해당하면 deep path가 필요하다고 판정한다:
#   1) 검색 top 점수가 임계값(기본 0.25) 미만 → 관련 문서를 못 찾은 것
#   2) 검색된 chunk 수가 최소 개수(기본 2개) 미만 → 근거가 부족한 것
#   3) 질문 유형이 COMPARISON/CAUSE/EXCEPTION → 복잡한 추론이 필요한 것
# 반환값: (deep 필요 여부, 이유 목록)
def should_use_deep_path(
    query: str,
    top_score: float,
    evidence_count: int,
    thresholds: GateThresholds,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    q_type = detect_question_type(query)

    if top_score < thresholds.min_top_score:
        reasons.append("low_top_score")
    if evidence_count < thresholds.min_evidence_chunks:
        reasons.append("insufficient_evidence")
    if q_type in {QuestionType.COMPARISON, QuestionType.CAUSE, QuestionType.EXCEPTION}:
        reasons.append("complex_question")

    return len(reasons) > 0, reasons


# LLM에 넘길 최종 프롬프트 문자열을 조립한다.
# 언어/질문유형별 헤더·출력형식 지시 + 유저 프로필 + 대화 히스토리
# + 검색된 근거 컨텍스트 + 출처 목록 + 유저 질문 순으로 구성된다.
def build_answer_prompt(
    *,
    language: str,
    question_type: QuestionType,
    query: str,
    context_block: str,
    evidence_lines: list[str],
    profile_text: str = "",
    history_block: str = "",
) -> str:
    header = _header(language)
    style = _style(language, question_type)
    evidence = "\n".join(f"- {line}" for line in evidence_lines[:8]) if evidence_lines else "- (none)"

    profile = f"\n[User Profile]\n{profile_text}\n" if profile_text else ""
    history = f"\n[Recent Conversation]\n{history_block}\n" if history_block else ""

    return (
        f"{header}\n"
        f"{style}\n"
        "Do not reveal chain-of-thought. Show only concise evidence summary.\n"
        "If evidence is weak, say uncertainty clearly and ask a focused follow-up question.\n"
        f"{profile}"
        f"{history}"
        "\n[Evidence Context]\n"
        f"{context_block}\n\n"
        "[Evidence Sources]\n"
        f"{evidence}\n\n"
        "[User Question]\n"
        f"{query}\n"
    )


# 검색 근거가 부족해서 답변하기 어려울 때 사용자에게 보여줄 메시지를 반환한다.
# 비자 유형·학교·마감일 같은 핵심 정보를 추가로 요청하는 내용.
def insufficient_evidence_message(language: str) -> str:
    if language == "ko":
        return (
            "현재 근거가 충분하지 않아 단정적으로 답변하기 어렵습니다. "
            "핵심 조건(비자 유형, 학교, 마감일)을 알려주시면 정확도를 높일 수 있습니다."
        )
    if language == "zh":
        return "目前证据不足，无法给出确定答案。请补充签证类型、学校和截止日期等关键信息。"
    return (
        "Evidence is currently insufficient for a confident answer. "
        "Please share key constraints such as visa type, school, and deadline."
    )


# 사용자가 비자 유형·학교 등 프로필 정보를 업데이트했을 때 확인 메시지를 반환한다.
# 저장된 프로필 내용을 그대로 출력해서 제대로 반영됐는지 확인할 수 있게 한다.
def status_update_message(language: str, profile_text: str) -> str:
    if language == "ko":
        return (
            "확인했습니다. 현재 사용자 정보는 아래와 같습니다.\n"
            f"{profile_text}\n"
            "이 정보를 기준으로 다음 질문에 더 정확히 답변하겠습니다."
        )
    if language == "zh":
        return (
            "已确认，当前用户信息如下：\n"
            f"{profile_text}\n"
            "接下来我会基于这些信息提供更准确的回答。"
        )
    return (
        "Confirmed. Current user profile:\n"
        f"{profile_text}\n"
        "I will use this profile for more accurate follow-up answers."
    )


# 쿼리 1개로 검색을 한 번 실행하고 결과를 반환한다.
# 검색 결과를 바탕으로 should_use_deep_path()를 호출해서
# deep path로 넘어가야 하는지 여부(use_deep)도 함께 반환한다.
# → query_runner에서 이 플래그를 보고 run_deep_path() 호출 여부를 결정해야 한다.
#   (현재 query_runner.py에는 이 연결이 아직 구현되지 않은 상태)
def run_fast_path(
    *,
    query: str,
    retrieve_fn: Callable[[str, int], tuple[list[tuple[Any, float]], list[str]]],
    top_k: int,
    thresholds: GateThresholds,
) -> dict[str, Any]:
    chunks, source_labels = retrieve_fn(query, top_k)
    best_score = float(chunks[0][1]) if chunks else 0.0
    evidence_count = len(chunks)
    use_deep, reasons = should_use_deep_path(query, best_score, evidence_count, thresholds)

    return {
        "path": "fast",
        "chunks": chunks,
        "source_labels": source_labels,
        "best_score": best_score,
        "evidence_count": evidence_count,
        "use_deep": use_deep,
        "reasons": reasons,
    }


# expand_query()로 만든 변형 쿼리 여러 개로 검색을 반복하고 결과를 병합한다.
# 같은 chunk가 여러 번 검색되면 가장 높은 점수 하나만 남긴다(중복 제거).
# 병합 후에도 근거가 부족하면(should_use_deep_path 재판정) 웹 크롤링으로 보충한다.
# → web_client.search_and_collect()가 외부 웹 검색 결과를 가져오는 진입점.
def run_deep_path(
    *,
    query_variants: list[str],
    retrieve_fn: Callable[[str, int], tuple[list[tuple[Any, float]], list[str]]],
    top_k: int,
    thresholds: GateThresholds,
    web_client: Optional[WebSearchClient] = None,
    enable_external: bool = True,
) -> dict[str, Any]:
    merged: dict[str, tuple[Any, float]] = {}
    merged_sources: list[str] = []

    for q in query_variants:
        chunks, source_labels = retrieve_fn(q, top_k)
        for ch, score in chunks:
            cid = getattr(ch, "chunk_id", None) or hash(getattr(ch, "text", ""))
            prev = merged.get(str(cid))
            if prev is None or score > prev[1]:
                merged[str(cid)] = (ch, float(score))
        for s in source_labels:
            if s not in merged_sources:
                merged_sources.append(s)

    ranked = sorted(merged.values(), key=lambda x: x[1], reverse=True)[:top_k]
    best_score = float(ranked[0][1]) if ranked else 0.0
    evidence_count = len(ranked)
    needs_more, reasons = should_use_deep_path(
        query_variants[0] if query_variants else "",
        best_score,
        evidence_count,
        thresholds,
    )

    external_contexts: list[str] = []
    if enable_external and needs_more and web_client is not None:
        snippets = web_client.search_and_collect(query_variants[0] if query_variants else "", max_results=3)
        for sn in snippets:
            external_contexts.append(f"[WEB] {sn.title}: {sn.snippet}")
            label = f"{sn.title} ({sn.url})"
            if label not in merged_sources:
                merged_sources.append(label)

    return {
        "path": "deep",
        "chunks": ranked,
        "source_labels": merged_sources,
        "external_contexts": external_contexts,
        "best_score": best_score,
        "evidence_count": evidence_count,
        "reasons": reasons,
    }


# 처리 경로(fast/deep), 응답 시간, 검색 점수 등을 JSONL 파일에 한 줄씩 기록한다.
# 나중에 fast/deep 비율, 평균 응답 시간 같은 운영 통계를 뽑는 데 사용한다.
def append_latency_log(
    *,
    log_path: str,
    agent: str,
    path: str,
    elapsed: float,
    best_score: float,
    evidence_count: int,
) -> None:
    record = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "agent": agent,
        "path": path,
        "elapsed_sec": elapsed,
        "best_score": round(best_score, 4),
        "evidence_count": evidence_count,
    }
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# LLM 시스템 프롬프트의 첫 줄(역할 지시)을 언어별로 반환한다.
# '근거 기반으로만 답하고 불확실하면 명시하라'는 핵심 지시가 들어있다.
def _header(language: str) -> str:
    if language == "ko":
        return (
            "당신은 유학생 안내 도우미입니다. 질문 언어와 동일한 언어로 답하세요. "
            "근거 문서 기반으로만 답변하고, 근거가 약하면 불확실성을 명시하세요."
        )
    if language == "zh":
        return (
            "你是留学生事务助手。请使用与用户输入相同的语言回答。"
            "仅基于证据内容作答，证据不足时明确说明不确定性。"
        )
    return (
        "You are an assistant for international students. Respond in the same language as the user. "
        "Answer only from evidence and state uncertainty when evidence is weak."
    )


# LLM에게 줄 출력 형식 지시를 언어·질문유형에 맞게 반환한다.
# 기본 형식(핵심답변/할일/서류/기한/근거요약)에 비교형·원인형·예외형일 때
# 해당 유형에 맞는 추가 지시를 덧붙인다.
def _style(language: str, question_type: QuestionType) -> str:
    if language == "ko":
        base = (
            "출력 형식:\n"
            "1) 핵심 답변\n"
            "2) 지금 해야 할 일(번호 목록)\n"
            "3) 준비 서류/확인 항목\n"
            "4) 기한/주의사항\n"
            "5) 근거 요약(출처 기반 요약만)"
        )
    elif language == "zh":
        base = (
            "输出格式：\n"
            "1) 核心回答\n"
            "2) 现在要做的事（编号列表）\n"
            "3) 材料/确认事项\n"
            "4) 时限/注意事项\n"
            "5) 证据摘要（仅来源摘要）"
        )
    else:
        base = (
            "Output format:\n"
            "1) Core answer\n"
            "2) Actions to take now (numbered)\n"
            "3) Required documents/checklist\n"
            "4) Deadline/cautions\n"
            "5) Evidence summary (source-grounded only)"
        )

    q_hint = {
        QuestionType.COMPARISON: {
            "ko": "질문 유형: 비교형. 항목별 차이를 표기하세요.",
            "zh": "问题类型：比较型。请按项目对比差异。",
            "en": "Question type: comparison. Contrast key differences by item.",
        },
        QuestionType.CAUSE: {
            "ko": "질문 유형: 원인형. 원인과 대응책을 분리해 적으세요.",
            "zh": "问题类型：原因型。请区分原因与应对措施。",
            "en": "Question type: cause. Separate causes from actions.",
        },
        QuestionType.EXCEPTION: {
            "ko": "질문 유형: 예외형. 일반 규칙과 예외 조건을 구분하세요.",
            "zh": "问题类型：例外型。区分一般规则与例外条件。",
            "en": "Question type: exception. Distinguish default rule and exceptions.",
        },
    }.get(question_type)

    if not q_hint:
        return base
    key = language if language in q_hint else "en"
    return f"{base}\n{q_hint[key]}"


# 텍스트에 terms 리스트 중 하나라도 포함되어 있으면 True를 반환한다.
# detect_question_type()의 키워드 매칭에서 내부적으로 사용한다.
def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)