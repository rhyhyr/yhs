"""
graph_rag/scheduler/freshness.py

역할:
- 주 1회 등록된 URL을 크롤링하여 콘텐츠 해시를 비교한다.
- 해시가 변경된 경우 해당 source_file 기반 노드 전체에 needs_review=true 플래그.
- APScheduler 기반으로 백그라운드에서 동작한다.
- 신선도 관리는 계획서 7.4절과 리스크 10(정보 신선도 자동 감지 부재)의 대응 전략이다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from graph_rag.config import FRESHNESS_CHECK_INTERVAL_WEEKS
from graph_rag.db.graph_store import GraphStore
from graph_rag.pipeline.loader import WebLoader

logger = logging.getLogger(__name__)

# 해시 저장 경로
_HASH_STORE_PATH = Path("data/url_hashes.json")

# 모니터링 대상 URL과 대응하는 source_file 이름
WATCHED_URLS: Dict[str, str] = {
    # url: source_file_name
    # 예시 (실제 URL로 교체 필요)
    "https://www.hikorea.go.kr/info/InfoDatail.pt?category_id=2&parent_id=385&catseq=&group_id=": "hikorea_visa_guide.html",
}


def _load_hashes() -> Dict[str, str]:
    if _HASH_STORE_PATH.exists():
        with open(_HASH_STORE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_hashes(hashes: Dict[str, str]) -> None:
    _HASH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_HASH_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def run_freshness_check(store: GraphStore) -> None:
    """
    등록된 URL 목록을 순회하며 콘텐츠 해시 변경을 감지한다.
    변경된 경우 해당 source_file 기반 노드에 needs_review 플래그를 설정한다.
    """
    loader = WebLoader()
    stored_hashes = _load_hashes()
    new_hashes = dict(stored_hashes)
    flagged: list[str] = []

    for url, source_file in WATCHED_URLS.items():
        logger.info("신선도 확인: %s", url)
        current_hash = loader.get_content_hash(url)
        if not current_hash:
            logger.warning("해시 계산 실패 (연결 문제?): %s", url)
            continue

        old_hash = stored_hashes.get(url, "")
        if old_hash and old_hash != current_hash:
            logger.warning("콘텐츠 변경 감지: %s → needs_review 플래그 설정", url)
            store.flag_needs_review_by_source(source_file)
            flagged.append(source_file)

        new_hashes[url] = current_hash

    _save_hashes(new_hashes)
    if flagged:
        logger.info("needs_review 플래그 설정 완료: %s", flagged)
    else:
        logger.info("신선도 확인 완료: 변경 없음")


class FreshnessScheduler:
    """APScheduler 기반 신선도 자동 감지 스케줄러."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store
        self._scheduler = None

    def start(self) -> None:
        """주 1회 신선도 확인 스케줄러를 시작한다."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:
            raise ImportError("apscheduler를 설치하세요: pip install apscheduler")

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            func=lambda: run_freshness_check(self._store),
            trigger="interval",
            weeks=FRESHNESS_CHECK_INTERVAL_WEEKS,
            id="freshness_check",
            name="URL 콘텐츠 신선도 확인",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            "신선도 스케줄러 시작: 주 %d회 실행",
            FRESHNESS_CHECK_INTERVAL_WEEKS,
        )

    def run_now(self) -> None:
        """즉시 신선도 확인을 실행한다 (수동 트리거용)."""
        run_freshness_check(self._store)

    def stop(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("신선도 스케줄러 종료")

    def add_url(self, url: str, source_file: str) -> None:
        """모니터링 대상 URL을 동적으로 추가한다."""
        WATCHED_URLS[url] = source_file
        logger.info("모니터링 URL 추가: %s → %s", url, source_file)
