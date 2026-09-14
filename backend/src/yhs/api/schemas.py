"""
yhs/api/schemas.py

HTTP 요청/응답 스키마.

프론트엔드(frontend/src/api/)와의 계약이므로, 필드를 바꿀 때는
반드시 양쪽을 함께 수정한다.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    """답변의 근거 출처 하나. 프론트의 출처 카드에 그대로 매핑된다."""

    id: str
    label: str                      # 문서명 (예: "하이코리아 외국인등록")
    detail: str = ""                # 위치 (예: "p.4 · 체류기간 연장")
    url: str = ""                   # 웹 출처일 때만 채워진다
    score: float = 0.0


class ChatMessage(BaseModel):
    role: str                       # "user" | "ai"
    content: str


class ChatRequest(BaseModel):
    message: str
    channel_id: str = Field(default="main", alias="channelId")
    history: list[ChatMessage] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    path: str = "fast"              # "fast" | "deep" — 프론트가 응답 속도 UI 에 사용
    model_config = {"populate_by_name": True}


# ── 구버전 계약 (유지) ────────────────────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
