"""인덱싱 파이프라인 공용 데이터 모델.

역할:
- Chunk: PDF에서 잘라낸 저장 단위
- CategoryNode: 계층 카테고리 노드(상/하위)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Chunk:
    """저장 대상 텍스트 조각과 임베딩을 담는 구조체."""
    chunk_id: str
    text: str
    page: int
    embedding: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass
class CategoryNode:
    """카테고리 노드 정보와 임베딩을 담는 구조체."""
    node_id: str
    name: str
    level: int
    keywords: list[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = field(default=None, repr=False)
