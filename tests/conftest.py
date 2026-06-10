import sys
from pathlib import Path
from unittest.mock import MagicMock

# 프로젝트 루트를 경로에 추가 (CI 환경에서 'agent' 모듈을 찾을 수 있도록)
sys.path.insert(0, str(Path(__file__).parent.parent))

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
