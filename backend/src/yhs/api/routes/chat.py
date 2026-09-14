"""
질의응답 엔드포인트.

  POST /api/chat  — 프론트엔드가 쓰는 계약 (근거 출처 포함)
  POST /query     — 구버전 계약. 기존 스크립트 호환을 위해 유지한다.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from yhs.api.deps import AppState
from yhs.api.schemas import AnswerResponse, ChatRequest, ChatResponse, QuestionRequest
from yhs.api.service import answer_question

router = APIRouter()


def _state(request: Request) -> AppState:
    state = getattr(request.app.state, "resources", None)
    if state is None:
        raise HTTPException(status_code=503, detail="서버가 아직 준비되지 않았습니다.")
    return state


@router.post("/api/chat", response_model=ChatResponse, tags=["chat"])
def chat(body: ChatRequest, request: Request) -> ChatResponse:
    answer = answer_question(_state(request), body.message)
    return ChatResponse(answer=answer.text, sources=answer.sources, path=answer.path)


@router.post("/query", response_model=AnswerResponse, tags=["chat"], deprecated=True)
def query(body: QuestionRequest, request: Request) -> AnswerResponse:
    """구버전 계약 — 근거 출처가 없다. 새 코드는 /api/chat 을 쓸 것."""
    answer = answer_question(_state(request), body.question)
    return AnswerResponse(answer=answer.text)
