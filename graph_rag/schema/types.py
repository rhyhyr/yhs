"""
graph_rag/schema/types.py

역할: 그래프 DB의 노드·엣지를 표현하는 Enum과 데이터클래스를 정의한다.
      DB 레이어와 파이프라인 레이어 사이의 공통 데이터 계약이다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ─── 노드 타입 ────────────────────────────────────────────────────────────────
class NodeType(str, Enum):
    DOMAIN = "Domain"
    TOPIC = "Topic"
    ENTITY = "Entity"
    PROCEDURE = "Procedure"
    DOCUMENT = "Document"
    INSTITUTION = "Institution"
    CHUNK = "Chunk"


# ─── 엣지 타입 ────────────────────────────────────────────────────────────────
class EdgeType(str, Enum):
    # 구조 레이어
    BELONGS_TO = "BELONGS_TO"
    CAN_TRANSITION_TO = "CAN_TRANSITION_TO"
    REQUIRES = "REQUIRES"
    NEXT_STEP = "NEXT_STEP"
    ENABLES_SHORTCUT = "ENABLES_SHORTCUT"
    ISSUED_BY = "ISSUED_BY"
    HANDLES = "HANDLES"
    RELATED_TO = "RELATED_TO"
    BLOCKS = "BLOCKS"
    # 원문 연결
    FOUND_IN = "FOUND_IN"
    MENTIONED_IN = "MENTIONED_IN"


# ─── 노드 데이터클래스 ────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now().isoformat()


@dataclass
class DomainNode:
    id: str
    name: str
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class TopicNode:
    id: str
    name: str
    domain: str
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class EntityNode:
    """구체적 개념 개체 (비자코드, 행정용어, 자격조건 등)"""
    id: str
    name: str
    domain: str
    aliases: List[str] = field(default_factory=list)
    summary: str = ""
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    last_verified: Optional[str] = None
    confidence: float = 1.0
    source: str = ""
    needs_review: bool = False
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class ProcedureNode:
    """단계적 절차 노드"""
    id: str
    name: str
    step_order: int
    parent_proc: str
    description: str = ""
    duration_est: str = ""
    domain: str = "visa"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class DocumentNode:
    """필요 서류 노드"""
    id: str
    name: str
    domain: str = "visa"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class InstitutionNode:
    """관련 기관 노드"""
    id: str
    name: str
    domain: str = "visa"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class ChunkNode:
    """원문 텍스트 조각 (Chunk Layer)"""
    id: str
    text: str
    source_file: str
    source_page: int
    section: str = ""
    language: str = "ko"
    doc_version: str = ""
    embedding: Optional[List[float]] = None  # numpy 변환 후 저장
    needs_review: bool = False
    created_at: str = field(default_factory=_now)


# ─── 엣지 데이터클래스 ────────────────────────────────────────────────────────
@dataclass
class Triple:
    """(Subject, Predicate, Object) 관계 트리플"""
    subject_id: str
    predicate: str          # EdgeType 값
    object_id: str
    confidence: float = 1.0
    source: str = ""
    source_page: int = 0
    condition: str = ""         # CAN_TRANSITION_TO 조건문
    mandatory: bool = True      # REQUIRES mandatory 여부
    block_reason: str = ""      # BLOCKS 사유
    relation_desc: str = ""     # RELATED_TO 관계 설명
    skip_to: str = ""           # ENABLES_SHORTCUT 건너뜀 대상
    step_order: int = 0         # NEXT_STEP 순서
    verified: bool = False
    needs_review: bool = False
    created_at: str = field(default_factory=_now)


@dataclass
class ChunkLink:
    """구조 노드 → Chunk 연결 (FOUND_IN / MENTIONED_IN)"""
    node_id: str
    node_type: str          # NodeType 값
    chunk_id: str
    link_type: str          # "FOUND_IN" | "MENTIONED_IN"
    confidence: float = 1.0
    source: str = ""
    created_at: str = field(default_factory=_now)


# ─── 파이프라인 내부 전달 객체 ────────────────────────────────────────────────
@dataclass
class RawDocument:
    """문서 수집 단계 출력"""
    text: str
    source_file: str
    source_page: int
    section: str = ""
    language: str = "ko"
    doc_version: str = ""
    source_url: str = ""


@dataclass
class RetrievalResult:
    """검색 엔진 최종 반환값"""
    triples: List[Triple]
    chunks: List[ChunkNode]
    retrieval_method: str       # "graph" | "vector" | "no_answer"
    entity_ids: List[str] = field(default_factory=list)
