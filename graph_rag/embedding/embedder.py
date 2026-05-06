"""
graph_rag/embedding/embedder.py

역할:
- BAAI/bge-m3 (100개 언어 지원) 임베딩 모델을 로컬에서 실행한다.
- Chunk 노드의 text를 배치로 인코딩하여 embedding 속성에 저장한다.
- 벡터 검색 및 Entity 링킹(summary 임베딩 비교)에서 사용한다.
- sentence-transformers GPU 가속 지원 (RTX 4070 가능).
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np

from graph_rag.config import (
    EMBEDDING_BATCH_SIZE, EMBEDDING_DIM, EMBEDDING_MODEL, EMBED_CACHE_PATH,
)

logger = logging.getLogger(__name__)


class Embedder:
    """BAAI/bge-m3 기반 텍스트 임베딩 생성기."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self._model_name = model_name or EMBEDDING_MODEL
        self._model = None  # 지연 로딩

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("임베딩 모델 로드 완료: %s", self._model_name)
        except ImportError:
            raise ImportError("sentence-transformers를 설치하세요: pip install sentence-transformers")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 목록을 배치 임베딩으로 변환한다.
        Returns:
            shape (N, EMBEDDING_DIM) numpy 배열
        """
        self._load_model()
        if not texts:
            return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)

        all_embeddings = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i: i + EMBEDDING_BATCH_SIZE]
            batch_emb = self._model.encode(
                batch,
                normalize_embeddings=True,  # 코사인 유사도를 내적으로 계산 가능
                show_progress_bar=False,
            )
            all_embeddings.append(batch_emb)
            logger.debug("임베딩 배치 %d/%d 완료", i // EMBEDDING_BATCH_SIZE + 1,
                         (len(texts) - 1) // EMBEDDING_BATCH_SIZE + 1)

        return np.vstack(all_embeddings).astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """단일 텍스트를 임베딩 벡터로 변환한다. shape: (DIM,)"""
        return self.encode([text])[0]

    def cosine_similarity(self, vec_a: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """
        vec_a (DIM,) 와 matrix (N, DIM) 간의 코사인 유사도를 계산한다.
        normalize_embeddings=True 적용 시 내적과 동일하다.
        Returns:
            shape (N,) 유사도 배열
        """
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        vec_a = vec_a / (np.linalg.norm(vec_a) + 1e-10)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        matrix_normed = matrix / norms
        return matrix_normed @ vec_a


# ─── 캐시 유틸 ───────────────────────────────────────────────────────────────
def save_embed_cache(data: dict, path: Optional[Path] = None) -> None:
    """임베딩 캐시를 pickle로 저장한다."""
    p = path or EMBED_CACHE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        pickle.dump(data, f)


def load_embed_cache(path: Optional[Path] = None) -> dict:
    """임베딩 캐시를 pickle에서 로드한다."""
    p = path or EMBED_CACHE_PATH
    if p.exists():
        with open(p, "rb") as f:
            return pickle.load(f)
    return {}
