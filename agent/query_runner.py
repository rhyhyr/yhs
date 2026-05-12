from __future__ import annotations

import logging
from datetime import datetime
from time import perf_counter

from agent.agent_runtime import (
    GateThresholds,
    append_latency_log,
    detect_language,
    detect_question_type,
    expand_query,
    insufficient_evidence_message,
    should_use_deep_path,
)
from agent.crawler.web_search_client import WebSearchClient
from agent.faq import FastPathHandler
from agent.gemini_runtime_client import GeminiRuntimeClient
from agent.retrieval_engine import RetrievalEngine
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder
from graph_rag.schema.types import ChunkNode, RetrievalResult

logger = logging.getLogger(__name__)

LOG_PATH = "logs/latency.jsonl"


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _merge_results(base: RetrievalResult, extras: list[RetrievalResult]) -> RetrievalResult:
    """여러 검색 결과를 병합하여 점수 기준 상위 청크만 남긴다.
    같은 chunk_id가 여러 번 나오면 가장 높은 점수 하나만 유지한다.
    """
    seen: dict[str, ChunkNode] = {}
    for c in base.chunks:
        if c.id:
            seen[c.id] = c

    for r in extras:
        for c in r.chunks:
            if not c.id:
                continue
            if c.id not in seen or c.score > seen[c.id].score:
                seen[c.id] = c

    merged_chunks = sorted(seen.values(), key=lambda x: x.score, reverse=True)[:4]

    # 병합된 방법명 결정
    all_methods = {base.retrieval_method} | {r.retrieval_method for r in extras}
    all_methods.discard("no_answer")
    if len(all_methods) > 1:
        method = "hybrid"
    elif all_methods:
        method = all_methods.pop()
    else:
        method = "no_answer"

    return RetrievalResult(
        triples=base.triples,
        chunks=merged_chunks,
        retrieval_method=method if merged_chunks else "no_answer",
        entity_ids=base.entity_ids,
    )


def run_query_loop() -> None:
    """대화형 질의 루프를 실행한다.

    처리 흐름:
      1. FAQ 키워드 매칭 (faq.py) → 히트 시 즉시 반환
      2. 언어 · 질문유형 감지 (agent_runtime.py)
      3. Fast Path: 단일 retrieve → should_use_deep_path() 판정
      4. Deep Path (필요 시): 변형 쿼리 병합 → 웹 크롤링 fallback
      5. 컨텍스트 조합 → LLM 답변 생성
      6. 지연 로그 기록 (logs/latency.jsonl)
    """
    embedder = Embedder()
    faq_handler = FastPathHandler()
    llm = GeminiRuntimeClient()
    web_client = WebSearchClient()
    thresholds = GateThresholds.from_env()

    if not llm.is_available():
        logger.warning("Gemini를 사용할 수 없습니다. FAQ 모드로만 동작합니다.")
        llm = None

    print("\n" + "=" * 60)
    print("  동아대학교 유학생 지원 AI 에이전트")
    print("  종료: 'quit' 또는 'exit' 입력")
    print("=" * 60 + "\n")
    qid = 0

    with GraphStore() as store:
        engine = RetrievalEngine(store, embedder, ollama_client=llm)

        while True:
            try:
                question = input("질문: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"[{_ts()}] 종료합니다.")
                break

            if not question:
                continue
            if question.lower() in ("quit", "exit", "종료"):
                print(f"[{_ts()}] 종료합니다.")
                break

            question_start = perf_counter()
            qid += 1
            print(f"\n[{_ts()}] 질문 입력: {question}")

            # ── 1. FAQ 빠른 매칭 ─────────────────────────────────────────────
            faq_start = perf_counter()
            print(f"[{_ts()}] FAQ 검사 시작")
            faq_answer = faq_handler.match(question)
            print(f"[{_ts()}] FAQ 검사 완료 ({perf_counter() - faq_start:.2f}s)")

            if faq_answer:
                print(f"[{_ts()}] [FAQ 빠른 답변]")
                print(faq_answer)
                print(f"[{_ts()}] 처리 완료 ({perf_counter() - question_start:.2f}s)\n")
                continue

            # ── 2. 언어 · 질문유형 감지 ──────────────────────────────────────
            language = detect_language(question)
            q_type = detect_question_type(question)
            print(f"[{_ts()}] 언어={language}, 질문유형={q_type.value}")

            # ── 3. Fast Path: 단일 검색 ──────────────────────────────────────
            retrieve_start = perf_counter()
            print(f"[{_ts()}] [FAST] 검색 시작")
            result = engine.retrieve(question)
            elapsed_fast = perf_counter() - retrieve_start
            print(
                f"[{_ts()}] [FAST] 검색 완료 ({elapsed_fast:.2f}s, "
                f"method={result.retrieval_method}, chunks={len(result.chunks)})"
            )

            best_score = max((c.score for c in result.chunks), default=0.0)
            evidence_count = len(result.chunks)
            use_deep, reasons = should_use_deep_path(
                question, best_score, evidence_count, thresholds
            )

            # ── 4. Deep Path: 변형 쿼리 병합 + 웹 크롤링 ───────────────────
            external_contexts: list[str] = []
            path = "fast"

            if use_deep:
                path = "deep"
                print(f"[{_ts()}] [DEEP] 진입 (이유: {reasons})")
                deep_start = perf_counter()

                # 변형 쿼리로 추가 검색 후 결과 병합
                variants = expand_query(question, language)[1:]  # 원본(첫 번째) 제외
                extra_results: list[RetrievalResult] = []
                for variant in variants:
                    v_result = engine.retrieve(variant)
                    if v_result.retrieval_method != "no_answer":
                        extra_results.append(v_result)

                if extra_results:
                    result = _merge_results(result, extra_results)
                    print(
                        f"[{_ts()}] [DEEP] 변형 쿼리 {len(variants)}개 병합 완료 "
                        f"(chunks={len(result.chunks)})"
                    )

                # 병합 후에도 근거 부족하면 웹 크롤링
                best_after = max((c.score for c in result.chunks), default=0.0)
                needs_web, _ = should_use_deep_path(
                    question, best_after, len(result.chunks), thresholds
                )
                if needs_web:
                    print(f"[{_ts()}] [DEEP] 웹 검색 시작")
                    snippets = web_client.search_and_collect(question, max_results=3)
                    for sn in snippets:
                        external_contexts.append(f"[WEB] {sn.title}: {sn.snippet}")
                    print(f"[{_ts()}] [DEEP] 웹 검색 완료 ({len(snippets)}개 수집)")

                print(f"[{_ts()}] [DEEP] 완료 ({perf_counter() - deep_start:.2f}s)")

            # ── 5. 근거 없음 처리 ────────────────────────────────────────────
            if result.retrieval_method == "no_answer" and not external_contexts:
                print(f"[{_ts()}] 근거 없음 → 안내 메시지 반환")
                print(insufficient_evidence_message(language))
                append_latency_log(
                    log_path=LOG_PATH, agent="yhs", path=path,
                    elapsed=perf_counter() - question_start,
                    best_score=best_score, evidence_count=evidence_count,
                )
                print(f"[{_ts()}] 처리 완료 ({perf_counter() - question_start:.2f}s)\n")
                continue

            # ── 6. 컨텍스트 조합 ─────────────────────────────────────────────
            context = engine.build_prompt_context(result)
            if external_contexts:
                context += "\n\n[외부 검색 결과]\n" + "\n".join(external_contexts)

            # ── 7. LLM 답변 생성 ─────────────────────────────────────────────
            answer_start = perf_counter()
            print(f"[{_ts()}] 답변 생성 시작")
            if llm:
                answer = llm.generate_answer(question, context, result)
            else:
                answer = (
                    f"[검색 방법: {result.retrieval_method} / 경로: {path}]\n\n{context}\n\n"
                    "※ LLM 서버가 없어 원문 컨텍스트를 직접 표시합니다."
                )
            print(f"[{_ts()}] 답변 생성 완료 ({perf_counter() - answer_start:.2f}s)")

            # 디버그: "정보 없음" 응답이면 검색된 청크 미리보기
            if "제공된 자료에서는 확인할 수 없습니다" in answer:
                print(f"[Q{qid}] retrieved chunks:")
                for i, c in enumerate(result.chunks[:4]):
                    preview = (c.text or "").replace("\n", " ")[:200]
                    print(f"  [{i}] score={c.score:.3f} | {preview}...")

            print(f"[{_ts()}] [{result.retrieval_method.upper()} / {path.upper()}]")
            print(answer)

            # ── 8. 지연 로그 기록 ────────────────────────────────────────────
            total_elapsed = perf_counter() - question_start
            append_latency_log(
                log_path=LOG_PATH, agent="yhs", path=path,
                elapsed=total_elapsed,
                best_score=best_score,
                evidence_count=evidence_count,
            )
            print(f"[{_ts()}] 처리 완료 ({total_elapsed:.2f}s)\n")

    web_client.close()
    if llm is not None:
        llm.close()
