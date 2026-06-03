import sys
from unittest.mock import MagicMock

MOCK_MODULES = [
    # 외부 패키지
    "google",
    "google.genai",
    "google.genai.types",
    "neo4j",
    "sentence_transformers",
    "faiss",
    "langchain",
    "langchain_community",
    "langchain_openai",
    "langchain_text_splitters",
    "pdfplumber",
    "pypdf",
    "openai",
    "sklearn",
    "sklearn.metrics",
    "sklearn.metrics.pairwise",
    "numpy",
    "bs4",
    "requests",
    # graph_rag 서브모듈
    "graph_rag",
    "graph_rag.config",
    "graph_rag.db",
    "graph_rag.db.graph_store",
    "graph_rag.embedding",
    "graph_rag.embedding.embedder",
    "graph_rag.llm",
    "graph_rag.llm.gemini_client",
    "graph_rag.llm.openai_client",
    "graph_rag.pipeline",
    "graph_rag.pipeline.chunker",
    "graph_rag.pipeline.cleaner",
    "graph_rag.pipeline.extractor",
    "graph_rag.pipeline.ingestor",
    "graph_rag.pipeline.loader",
    "graph_rag.scheduler",
    "graph_rag.scheduler.freshness",
    "graph_rag.schema",
    "graph_rag.schema.types",
]

for mod in MOCK_MODULES:
    sys.modules[mod] = MagicMock()
