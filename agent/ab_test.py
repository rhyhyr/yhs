"""
Week11 - A/B 테스트 사용자 배정 + 이벤트 추적

특징:
- 같은 user_id + experiment 조합은 항상 같은 variant (해시 기반)
- 이벤트 로그는 logs/ab_events.jsonl에 추가
"""
import hashlib
import json
import os
from datetime import datetime, timezone


def assign_variant(user_id: str, experiment: str, variants: list[str]) -> str:
    """
    사용자 ID 해시로 variant 일관 배정.
    - 같은 유저는 재방문해도 동일 variant
    - variants 리스트 순서가 바뀌면 배정도 바뀔 수 있음
    """
    key = f"{experiment}:{user_id}".encode()
    bucket = int(hashlib.md5(key).hexdigest(), 16) % len(variants)
    return variants[bucket]


def track_event(
    user_id: str,
    experiment: str,
    variant: str,
    event: str,
    metadata: dict | None = None,
) -> dict:
    """이벤트를 JSONL 파일에 기록하고 로그 엔트리를 반환"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "experiment": experiment,
        "variant": variant,
        "event": event,
        **(metadata or {}),
    }
    log_path = os.path.join("logs", "ab_events.jsonl")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


# ──────────────────────────────────────────────
# 등록된 실험 목록
# ──────────────────────────────────────────────
EXPERIMENTS = {
    "response_format": {
        "description": "응답 포맷 A/B 테스트",
        "variants": ["control", "verbose"],
    },
    "search_algorithm": {
        "description": "검색 알고리즘 A/B 테스트",
        "variants": ["vector", "hybrid"],
    },
}
