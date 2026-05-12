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

    args = parser.parse_args()

    if not any([args.ingest, args.query, args.embed_update]):
        parser.print_help()
        sys.exit(0)

    if args.ingest:
        run_ingest(args.pdf_dir, use_llm=not args.no_llm)

    if args.embed_update:
        run_embed_update()

    if args.query:
        run_query_loop()


if __name__ == "__main__":
    main()
