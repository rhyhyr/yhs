from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from agent.ingest_runner import run_embed_update, run_ingest
from agent.query_runner import run_query_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="YHS graph RAG agent")
    parser.add_argument("--ingest", action="store_true", help="PDF 파일을 인제스트한다")
    parser.add_argument("--pdf-dir", type=Path, default=None, help="PDF 디렉토리 경로")
    parser.add_argument("--query", action="store_true", help="대화형 질의 루프를 시작한다")
    parser.add_argument("--no-llm", action="store_true", help="LLM 없이 규칙 기반만 사용")
    parser.add_argument("--embed-update", action="store_true", help="누락된 임베딩을 일괄 생성한다")
    parser.add_argument("--freshness-check", action="store_true", help="즉시 신선도 확인을 실행한다")
    parser.add_argument("--with-scheduler", action="store_true", help="신선도 스케줄러를 백그라운드로 시작한다")

    args = parser.parse_args()

    if not any([args.ingest, args.query, args.embed_update, args.freshness_check]):
        parser.print_help()
        sys.exit(0)

    scheduler = None
    if args.with_scheduler or args.freshness_check:
        from graph_rag.db.graph_store import GraphStore
        from graph_rag.scheduler.freshness import FreshnessScheduler

        store = GraphStore()
        scheduler = FreshnessScheduler(store)
        if args.freshness_check:
            scheduler.run_now()
        if args.with_scheduler:
            scheduler.start()

    try:
        if args.ingest:
            run_ingest(args.pdf_dir, use_llm=not args.no_llm)

        if args.embed_update:
            run_embed_update()

        if args.query:
            run_query_loop()

    finally:
        if scheduler:
            scheduler.stop()


if __name__ == "__main__":
    main()