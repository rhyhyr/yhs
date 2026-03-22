"""
Hierarchical PDF Indexer entrypoint.

역할:
- PDF 폴더를 스캔
- 신규 PDF만 Neo4j 계층 그래프에 저장
- 검색/답변 기능은 포함하지 않음
"""

from __future__ import annotations

from indexing import PDF_DIR, IndexingPipeline


if __name__ == "__main__":
    pipeline = IndexingPipeline()
    try:
        pipeline.run(PDF_DIR)
    finally:
        pipeline.close()
