"""
yhs/api/main.py

FastAPI 애플리케이션.

    uvicorn yhs.api.main:app --host 0.0.0.0 --port 8000

무거운 리소스(임베딩 모델, Neo4j 드라이버)는 lifespan 에서 한 번만 만들고
app.state.resources 에 담아 둔다. 라우트는 거기서 꺼내 쓴다.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yhs import __version__
from yhs.api.deps import AppState
from yhs.api.routes import chat_router, health_router
from yhs.core.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("리소스 초기화 시작 (임베딩 모델 + Neo4j)")
    app.state.resources = AppState.create()
    logger.info("초기화 완료 — 요청을 받을 준비가 됐습니다.")
    try:
        yield
    finally:
        app.state.resources.close()
        app.state.resources = None
        logger.info("리소스 정리 완료")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="동아대 유학생 AI 에이전트",
        version=__version__,
        lifespan=lifespan,
    )

    # 운영에서는 nginx 가 프론트와 /api 를 같은 오리진으로 묶으므로 CORS 가
    # 필요 없다. 개발 중 vite dev 서버(:5173)에서 직접 호출할 때를 위해
    # 허용 오리진을 설정으로 받는다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
