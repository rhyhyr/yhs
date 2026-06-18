from __future__ import annotations

import logging
import os

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent_runtime import (
    GateThresholds,
    detect_language,
    expand_query,
    insufficient_evidence_message,
    should_use_deep_path,
)
from agent.crawler.web_search_client import WebSearchClient, allowed_sites
from agent.faq import FastPathHandler
from agent.retrieval_engine import RetrievalEngine
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="동아대 유학생 AI 에이전트")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


def _build_llm():
    """RUNTIME_LLM 환경변수에 따라 적절한 LLM 클라이언트를 반환한다."""
    provider = os.environ.get("RUNTIME_LLM", "ollama").lower()
    if provider == "gemini":
        from agent.gemini_runtime_client import GeminiRuntimeClient
        client = GeminiRuntimeClient()
        if not client.is_available():
            logger.warning("Gemini API 키 없음 — Ollama로 폴백합니다.")
            provider = "ollama"
        else:
            return client
    if provider == "hf":
        from agent.hf_runtime_client import HFRuntimeClient
        return HFRuntimeClient()
    # 기본값: ollama
    from agent.ollama_runtime_client import OllamaRuntimeClient
    client = OllamaRuntimeClient()
    if not client.is_available():
        logger.warning("Ollama 서버에 연결할 수 없습니다. 'ollama serve' 실행 여부를 확인하세요.")
    return client


# 서버 시작/종료 시 리소스 관리 (GraphStore 연결 유지)
embedder = Embedder()
faq_handler = FastPathHandler()
llm = _build_llm()
thresholds = GateThresholds.from_env()
http_session = requests.Session()
_store: GraphStore | None = None
_engine = None
_web_client = None


@app.on_event("startup")
def startup():
    global _store, _engine, _web_client
    _store = GraphStore()
    _store.__enter__()
    _engine = RetrievalEngine(_store, embedder, ollama_client=llm)
    _web_client = WebSearchClient(http_session, embedder, llm, _store._driver, allowed_sites, openai_client=None)
    logger.info("startup complete")


@app.on_event("shutdown")
def shutdown():
    if _store:
        _store.__exit__(None, None, None)
    http_session.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=AnswerResponse)
def query(body: QuestionRequest):
    question = body.question.strip()
    if not question:
        return AnswerResponse(answer="질문을 입력해주세요.")

    faq_answer = faq_handler.match(question)
    if faq_answer:
        return AnswerResponse(answer=faq_answer)

    language = detect_language(question)

    result = _engine.retrieve(question)
    best_score = max((c.score for c in result.chunks), default=0.0)
    use_deep, _ = should_use_deep_path(question, best_score, len(result.chunks), thresholds)

    external_contexts: list[str] = []

    if use_deep:
        variants = expand_query(question, language)[1:]
        extra_results = [r for v in variants for r in [_engine.retrieve(v)] if r.retrieval_method != "no_answer"]
        if extra_results:
            from agent.query_runner import _merge_results
            result = _merge_results(result, extra_results)

        best_after = max((c.score for c in result.chunks), default=0.0)
        needs_web, _ = should_use_deep_path(question, best_after, len(result.chunks), thresholds)
        if needs_web:
            snippets = _web_client.search_and_collect(question, max_results=3)
            external_contexts = [f"[WEB] {sn.title}: {sn.snippet}" for sn in snippets]

    if result.retrieval_method == "no_answer" and not external_contexts:
        return AnswerResponse(answer=insufficient_evidence_message(language))

    context = _engine.build_prompt_context(result)
    if external_contexts:
        context += "\n\n[외부 검색 결과]\n" + "\n".join(external_contexts)

    if llm and llm.is_available():
        answer = llm.generate_answer(question, context, result, web_context=bool(external_contexts))
    else:
        answer = context

    return AnswerResponse(answer=answer)
