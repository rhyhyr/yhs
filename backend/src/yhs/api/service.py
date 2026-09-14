"""
yhs/api/service.py

질의 → 답변 파이프라인. HTTP 계층과 분리해 두어 라우트가 얇게 유지된다.

흐름:
  1. FAQ 빠른 경로 — 즉답 가능한 단순 질문이면 검색 없이 반환
  2. 그래프 + 벡터 검색 (fast path)
  3. 근거가 부족하면 쿼리 확장 + 멀티 검색 (deep path)
  4. 그래도 부족하면 허용 사이트 웹 크롤링
  5. LLM 답변 생성 + 근거 출처 수집
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from yhs.api.deps import AppState
from yhs.api.schemas import Source
from yhs.rag.runtime import (
    detect_language,
    expand_query,
    insufficient_evidence_message,
    should_use_deep_path,
)
from yhs.schema.types import ChunkNode

logger = logging.getLogger(__name__)

# 응답에 실어 보낼 최대 출처 개수 (프론트 출처 카드가 감당할 수 있는 수준)
_MAX_SOURCES = 5


@dataclass
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)
    path: str = "fast"          # "fast" | "deep"


def _pretty_label(source_file: str) -> str:
    """'26_동아대_장학금_학부_한국어트랙.pdf' → '동아대 장학금 학부 한국어트랙'."""
    name = source_file.rsplit(".", 1)[0]
    if "_" in name and name.split("_", 1)[0].isdigit():
        name = name.split("_", 1)[1]
    return name.replace("_", " ")


def _chunk_to_source(chunk: ChunkNode) -> Source:
    detail_parts = []
    if chunk.source_page:
        detail_parts.append(f"p.{chunk.source_page}")
    if chunk.section:
        detail_parts.append(chunk.section)
    if chunk.doc_version:
        detail_parts.append(chunk.doc_version)
    return Source(
        id=chunk.id,
        label=_pretty_label(chunk.source_file),
        detail=" · ".join(detail_parts),
        score=round(chunk.score, 4),
    )


def answer_question(state: AppState, question: str) -> Answer:
    """질문 하나에 대한 답변과 근거를 만든다."""
    question = question.strip()
    if not question:
        return Answer(text="질문을 입력해주세요.")

    # 1. FAQ 빠른 경로
    faq_answer = state.faq.match(question)
    if faq_answer:
        return Answer(text=faq_answer)

    language = detect_language(question)

    # 2. fast path 검색
    result = state.engine.retrieve(question)
    best_score = max((c.score for c in result.chunks), default=0.0)
    use_deep, _ = should_use_deep_path(question, best_score, len(result.chunks), state.thresholds)

    path = "deep" if use_deep else "fast"
    external: list[tuple[str, str, str]] = []   # (title, snippet, url)

    # 3~4. deep path — 쿼리 확장 후에도 부족하면 웹 크롤링
    if use_deep:
        variants = expand_query(question, language)[1:]
        extra = [r for v in variants for r in [state.engine.retrieve(v)]
                 if r.retrieval_method != "no_answer"]
        if extra:
            from yhs.rag.query_runner import _merge_results

            result = _merge_results(result, extra)

        best_after = max((c.score for c in result.chunks), default=0.0)
        needs_web, _ = should_use_deep_path(
            question, best_after, len(result.chunks), state.thresholds
        )
        if needs_web:
            snippets = state.web_client.search_and_collect(question, max_results=3)
            external = [(sn.title, sn.snippet, sn.url) for sn in snippets]

    if result.retrieval_method == "no_answer" and not external:
        return Answer(text=insufficient_evidence_message(language), path=path)

    # 5. 컨텍스트 조합 → 생성
    context = state.engine.build_prompt_context(result)
    if external:
        context += "\n\n[외부 검색 결과]\n" + "\n".join(
            f"[WEB] {title}: {snippet}" for title, snippet, _ in external
        )

    if state.llm and state.llm.is_available():
        text = state.llm.generate_answer(
            question, context, result, web_context=bool(external)
        )
    else:
        # LLM 을 못 쓰면 검색 컨텍스트라도 그대로 돌려준다 (디버깅 목적)
        logger.warning("LLM 을 사용할 수 없어 검색 컨텍스트를 그대로 반환합니다.")
        text = context

    sources = [_chunk_to_source(c) for c in result.chunks[:_MAX_SOURCES]]
    sources += [
        Source(id=f"web-{i}", label=title or url, detail="웹 검색", url=url)
        for i, (title, _, url) in enumerate(external)
    ]

    return Answer(text=text, sources=sources[:_MAX_SOURCES], path=path)
