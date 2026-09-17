"""
yhs/ingest/llm/json_repair.py

LLM 응답을 JSON 으로 파싱하는 공통 로직.

왜 분리했나:
    exaone_kb_client 와 gemini_client 가 "바로 파싱 시도 → 실패하면
    json_repair 로 복구 → 그래도 실패하면 포기" 를 각자 구현하고
    있었다. 두 곳이 같은 논리로 어긋나기 전에 한 곳으로 모은다.
"""

from __future__ import annotations

import json
from typing import Any


def parse_json_with_repair(raw: str) -> tuple[dict[str, Any] | None, bool]:
    """raw 를 JSON 으로 파싱한다.

    Returns: (파싱 결과 또는 실패 시 None, repair 를 거쳤는지 여부)
    """
    try:
        return json.loads(raw), False
    except json.JSONDecodeError:
        pass

    try:
        from json_repair import repair_json
        return json.loads(repair_json(raw)), True
    except Exception:
        return None, False
