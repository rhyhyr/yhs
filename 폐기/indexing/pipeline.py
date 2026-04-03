"""폴더 단위 인덱싱 파이프라인 모듈.

역할:
- 실행 환경 검증 및 컴포넌트 조립
- PDF 폴더 스캔 후 신규 파일만 Indexer에 전달
- 실행 결과(저장/스킵/실패) 집계 출력
"""

from __future__ import annotations

import glob
import os

import google.generativeai as genai

from .categorizer import CategoryExtractor
from .config import (
    GEMINI_API_KEY,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    PDF_DIR,
    build_gemini_model,
    validate_env,
)
from .embedder import build_embedder
from .indexer import Indexer
from .store import Neo4jConnector


class IndexingPipeline:
    """여러 PDF를 순회하며 누적 인덱싱을 수행하는 실행 파이프라인."""
    def __init__(self) -> None:
        validate_env()

        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = build_gemini_model()

        self._neo4j = Neo4jConnector(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        self._neo4j.create_indexes()

        embedder = build_embedder()

        extractor = CategoryExtractor(gemini_model)
        self._indexer = Indexer(self._neo4j, extractor, embedder)

    def run(self, pdf_dir: str = PDF_DIR) -> None:
        pattern = os.path.join(pdf_dir, "*.pdf")
        pdf_files = sorted(glob.glob(pattern))

        if not pdf_files:
            print(f"[경고] PDF 파일 없음: {pdf_dir}")
            return

        print(f"\n📁 폴더: {pdf_dir}")
        print(f"   발견: {len(pdf_files)}개 PDF\n")

        saved = skipped = failed = 0

        for pdf_path in pdf_files:
            try:
                if self._indexer.run(pdf_path):
                    saved += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  [오류] {os.path.basename(pdf_path)} 처리 실패: {e}")
                failed += 1

        counts = self._neo4j.count_summary()
        print(f"\n{'═'*55}")
        print("  DB 저장 완료")
        print(f"  이번 실행: 저장 {saved}개 / 스킵 {skipped}개 / 실패 {failed}개")
        print(
            f"  DB 누적:   Document={counts['Document']}  "
            f"Category={counts['Category']}  Chunk={counts['Chunk']}"
        )
        print(f"{'═'*55}\n")

    def close(self) -> None:
        self._neo4j.close()
