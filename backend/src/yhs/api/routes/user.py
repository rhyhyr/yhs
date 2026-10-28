"""
사용자 프로필 저장 — GET/PUT /api/user/profile.

인증이 아직 없어서 브라우저마다 만든 X-Client-Id 헤더로 프로필을 나눈다.
파일 이름은 ID 의 해시라서 헤더 값이 경로에 그대로 들어가지 않는다.
# ponytail: 클라이언트 ID 는 위조 가능 — 로그인 도입 시 토큰 기준으로 바꾼다.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from yhs.core.settings import get_settings

router = APIRouter(tags=["user"])


def _client_id(x_client_id: str | None) -> str:
    if not x_client_id or len(x_client_id) > 128:
        raise HTTPException(status_code=400, detail="X-Client-Id 헤더가 필요합니다.")
    return x_client_id


def _profile_path(client_id: str) -> Path:
    digest = hashlib.sha256(client_id.encode("utf-8")).hexdigest()
    return get_settings().data_dir / "user_profiles" / f"{digest}.json"


@router.get("/api/user/profile")
def get_profile(x_client_id: str | None = Header(default=None)) -> dict[str, Any]:
    path = _profile_path(_client_id(x_client_id))
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@router.put("/api/user/profile")
def put_profile(body: dict[str, Any], x_client_id: str | None = Header(default=None)) -> dict[str, Any]:
    languages = body.get("languages", [])
    if not isinstance(languages, list) or not all(isinstance(lang, str) for lang in languages):
        raise HTTPException(status_code=422, detail="languages 는 문자열 배열이어야 합니다.")

    path = _profile_path(_client_id(x_client_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)  # 쓰는 도중 끊겨도 기존 파일이 깨지지 않게 교체
    return body
