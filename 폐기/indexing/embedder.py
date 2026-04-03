"""임베딩 생성 모듈.

역할:
- sentence-transformers 기반 임베더 초기화
- torch/모델 로딩 실패 시 HashingVectorizer 폴백 제공
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from .config import EMBED_MODEL

try:
    from sentence_transformers import SentenceTransformer
    _ST_ERROR: Optional[Exception] = None
except Exception as _e:
    SentenceTransformer = None  # type: ignore[assignment,misc]
    _ST_ERROR = _e


class FallbackEmbedder:
    """torch 없이 동작하는 경량 폴백 임베더."""
    def __init__(self, n_features: int = 768):
        self._vec = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            token_pattern=r"(?u)\b\w+\b",
        )

    def encode(self, texts: str | list[str], show_progress_bar: bool = False) -> np.ndarray:
        del show_progress_bar
        single = isinstance(texts, str)
        lst = [texts] if single else texts
        arr = self._vec.transform(lst).toarray().astype(np.float32)
        return arr[0] if single else arr


def build_embedder() -> Any:
    """우선 SentenceTransformer를 시도하고 실패하면 폴백 임베더를 반환한다."""
    if SentenceTransformer is None:
        print(
            "[WARN] sentence-transformers 로드 실패 -> 폴백 임베더 사용\n"
            f"       원인: {_ST_ERROR}"
        )
        return FallbackEmbedder()
    try:
        return SentenceTransformer(EMBED_MODEL)
    except Exception as e:
        print(f"[WARN] SentenceTransformer 초기화 실패 -> 폴백 임베더 사용\n       원인: {e}")
        return FallbackEmbedder()
