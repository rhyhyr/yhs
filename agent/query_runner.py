from __future__ import annotations

import logging
from datetime import datetime
from time import perf_counter

logger = logging.getLogger(__name__)


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_query_loop() -> None:
    """대화형 질의 루프를 실행한다."""
    from graph_rag.config import NO_ANSWER_RESPONSE
    from graph_rag.db.graph_store import GraphStore
    from graph_rag.embedding.embedder import Embedder
    from agent.faq import FastPathHandler
    from agent.ollama_client import OllamaRuntimeClient
    from agent.retrieval_engine import RetrievalEngine

    embedder = Embedder()
    faq_handler = FastPathHandler()

    print("\n" + "=" * 60)
    print("  동아대학교 유학생 지원 AI 에이전트")
    print("  종료: 'quit' 또는 'exit' 입력")
    print("=" * 60 + "\n")

    with GraphStore() as store:
        engine = RetrievalEngine(store, embedder)

        llm = OllamaRuntimeClient()
        if not llm.is_available():
            logger.warning("Ollama 서버를 찾을 수 없습니다. FAQ 모드로만 동작합니다.")
            llm = None

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
            print(f"\n[{_ts()}] 질문 입력: {question}")

            faq_start = perf_counter()
            print(f"[{_ts()}] FAQ 검사 시작")
            faq_answer = faq_handler.match(question)
            print(f"[{_ts()}] FAQ 검사 완료 ({perf_counter() - faq_start:.2f}s)")
            if faq_answer:
                print(f"[{_ts()}] [FAQ 빠른 답변]")
                print(faq_answer)
                print(f"[{_ts()}] 처리 완료 ({perf_counter() - question_start:.2f}s)\n")
                continue

            retrieve_start = perf_counter()
            print(f"[{_ts()}] 검색 시작")
            result = engine.retrieve(question)
            print(
                f"[{_ts()}] 검색 완료 ({perf_counter() - retrieve_start:.2f}s, "
                f"method={result.retrieval_method})"
            )

            if result.retrieval_method == "no_answer":
                print(NO_ANSWER_RESPONSE)
                print(f"[{_ts()}] 처리 완료 ({perf_counter() - question_start:.2f}s)\n")
                continue

            context_start = perf_counter()
            context = engine.build_prompt_context(result)
            print(f"[{_ts()}] 컨텍스트 조합 완료 ({perf_counter() - context_start:.2f}s)")

            answer_start = perf_counter()
            print(f"[{_ts()}] 답변 생성 시작")
            if llm:
                answer = llm.generate_answer(question, context, result)
            else:
                answer = (
                    f"[검색 방법: {result.retrieval_method}]\n\n{context}\n\n"
                    "※ LLM 서버가 없어 원문 컨텍스트를 직접 표시합니다."
                )
            print(f"[{_ts()}] 답변 생성 완료 ({perf_counter() - answer_start:.2f}s)")

            print(f"[{_ts()}] [{result.retrieval_method.upper()} 검색 결과]")
            print(answer)
            print(f"[{_ts()}] 처리 완료 ({perf_counter() - question_start:.2f}s)\n")
