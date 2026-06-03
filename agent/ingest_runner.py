from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_ingest(pdf_dir: Path, use_llm: bool = True) -> None:
    """PDF 디렉토리의 모든 PDF를 처리하여 그래프 DB에 적재한다."""
    from graph_rag.config import PDF_DIR
    from graph_rag.db.graph_store import GraphStore
    from graph_rag.embedding.embedder import Embedder
    from graph_rag.pipeline.chunker import chunk_document
    from graph_rag.pipeline.cleaner import clean_text
    from graph_rag.pipeline.extractor import HybridExtractor
    from graph_rag.pipeline.ingestor import GraphIngestor
    from graph_rag.pipeline.loader import PDFLoader

    target_dir = pdf_dir or PDF_DIR
    pdf_files = list(target_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning("PDF 파일이 없습니다: %s", target_dir)
        return

    logger.info("=== 인제스트 시작: %d개 PDF ===", len(pdf_files))

    pdf_loader = PDFLoader()
    extractor = HybridExtractor(use_llm=use_llm)
    embedder = Embedder()

    with GraphStore() as store:
        ingestor = GraphIngestor(store)

        for pdf_path in pdf_files:
            logger.info("처리 중: %s", pdf_path.name)

            raw_docs = pdf_loader.load(pdf_path)

            for doc in raw_docs:
                doc.text = clean_text(doc.text)

            all_chunks = []
            for doc in raw_docs:
                chunks = chunk_document(doc)
                all_chunks.extend(chunks)
            logger.info("청킹 완료: %d개 Chunk", len(all_chunks))

            texts = [c.text for c in all_chunks]
            embeddings = embedder.encode(texts)
            for chunk, emb in zip(all_chunks, embeddings):
                chunk.embedding = emb.tolist()

            entities, triples, chunk_links = extractor.extract_all(all_chunks)
            ingestor.ingest_all(all_chunks, entities, triples, chunk_links)

        logger.info("=== 인제스트 완료 ===")


def run_embed_update() -> None:
    """기존 Chunk에 임베딩이 없는 경우 배치로 생성한다."""
    from graph_rag.db.graph_store import GraphStore
    from graph_rag.embedding.embedder import Embedder
    from graph_rag.schema.types import ChunkNode

    embedder = Embedder()
    with GraphStore() as store:
        chunks = store.get_all_chunks_with_embeddings()
        no_embed = [c for c in chunks if not c.get("embedding")]
        if not no_embed:
            logger.info("모든 Chunk에 임베딩이 있습니다.")
            return

        logger.info("임베딩 생성 대상: %d개 Chunk", len(no_embed))
        texts = [c["text"] for c in no_embed]
        embeddings = embedder.encode(texts)

        for c_dict, emb in zip(no_embed, embeddings):
            chunk = ChunkNode(
                id=c_dict["id"],
                text=c_dict["text"],
                source_file=c_dict["source_file"],
                source_page=c_dict["source_page"],
                embedding=emb.tolist(),
            )
            store.upsert_chunk(chunk)

        logger.info("임베딩 업데이트 완료")
