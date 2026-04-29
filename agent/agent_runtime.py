from __future__ import annotations

import json
import os
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import requests
from bs4 import BeautifulSoup


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


@dataclass
class WebSnippet:
    url: str
    title: str
    snippet: str


def detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        if re.search(r"[가-힣]", text):
            return "ko"
        return "zh"
    if re.search(r"[가-힣]", text):
        return "ko"
    return "en"


def normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


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


class WebSearchClient:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.allowed_suffixes = self._load_allowed_suffixes()

    def close(self) -> None:
        self.session.close()

    def search_and_collect(self, query: str, max_results: int = 3) -> list[WebSnippet]:
        urls = self._search_urls(query, max_results=max_results * 3)
        snippets: list[WebSnippet] = []
        for u in urls:
            final_url = self._resolve_final_url(u)
            if not final_url:
                continue
            if not self._is_allowed_url(final_url):
                continue
            text = self._fetch_text(final_url)
            if not text:
                continue
            title = self._title_from_url(final_url)
            snippets.append(WebSnippet(url=final_url, title=title, snippet=text[:1200]))
            if len(snippets) >= max_results:
                break
        return snippets

    def _search_urls(self, query: str, max_results: int) -> list[str]:
        q = urllib.parse.quote(query)
        url = f"https://duckduckgo.com/html/?q={q}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        out: list[str] = []
        for a in soup.select("a.result__a"):
            href = (a.get("href") or "").strip()
            if href.startswith("http"):
                out.append(href)
            if len(out) >= max_results:
                break
        return out

    def _resolve_final_url(self, url: str) -> str:
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            return resp.url
        except Exception:
            return ""

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        return any(host == s or host.endswith(f".{s}") for s in self.allowed_suffixes)

    def _fetch_text(self, url: str) -> str:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ")).strip()

    @staticmethod
    def _title_from_url(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname or url

    @staticmethod
    def _load_allowed_suffixes() -> list[str]:
        env = os.environ.get(
            "ALLOWED_EXTERNAL_SUFFIXES",
            "go.kr,ac.kr,gov,edu,gov.cn,edu.cn,ac.uk,gov.uk",
        )
        return [x.strip().lower().lstrip(".") for x in env.split(",") if x.strip()]


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


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)