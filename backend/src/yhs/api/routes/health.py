"""헬스체크 — 도커 HEALTHCHECK 와 로드밸런서가 사용한다."""

from __future__ import annotations

from fastapi import APIRouter, Request

from yhs import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    """프로세스가 살아 있고 리소스 초기화가 끝났는지 알려준다."""
    ready = getattr(request.app.state, "resources", None) is not None
    return {"status": "ok" if ready else "starting", "version": __version__}
