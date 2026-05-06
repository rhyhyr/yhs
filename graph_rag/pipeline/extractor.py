"""
graph_rag/pipeline/extractor.py

역할:
- Chunk 목록에서 엔티티와 관계를 추출한다.
- 규칙 기반: 비자코드, 체류기간, 기관명 → confidence 1.0
- LLM 기반: OpenAI API를 통한 구조화 JSON 추출 → confidence 0.7~0.9
- 허용 predicate를 7개로 고정하여 스키마 밖 관계 생성을 방지한다.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Tuple

from graph_rag.config import ALLOWED_PREDICATES, KNOWN_INSTITUTIONS
from graph_rag.schema.types import ChunkNode, EntityNode, Triple

logger = logging.getLogger(__name__)

# ─── 규칙 기반 패턴 ───────────────────────────────────────────────────────────
_VISA_CODE_RE = re.compile(r"\b([A-Z]-\d+(?:-\d+)?)\b")
_DURATION_RE = re.compile(r"(\d+년|\d+개월|\d+일)")
_EXTEND_POSSIBLE_RE = re.compile(r"연장\s*가능")
_EXTEND_IMPOSSIBLE_RE = re.compile(r"연장\s*불가")
_SECTION_HEADER_RE = re.compile(r"(유형\d+|\d+단계|Part\s*\d+)", re.IGNORECASE)


class RuleBasedExtractor:
    """정규식 기반 엔티티 추출기 (confidence = 1.0)."""

    def extract_entities(self, chunk: ChunkNode) -> List[EntityNode]:
        entities: List[EntityNode] = []
        text = chunk.text

        # 비자 코드 추출
        for m in _VISA_CODE_RE.finditer(text):
            code = m.group(1)
            entities.append(EntityNode(
                id=code,
                name=code,
                domain="visa",
                summary=f"비자 코드 {code}",
                confidence=1.0,
                source=chunk.source_file,
            ))

        # 기관명 추출
        for inst in KNOWN_INSTITUTIONS:
            if inst in text:
                inst_id = inst.replace(" ", "_")
                entities.append(EntityNode(
                    id=inst_id,
                    name=inst,
                    domain="visa",
                    confidence=1.0,
                    source=chunk.source_file,
                ))

        return entities

    def extract_triples(self, chunk: ChunkNode) -> List[Triple]:
        """규칙 기반 관계 추출."""
        triples: List[Triple] = []
        text = chunk.text

        # 연장 가능/불가 패턴에서 BLOCKS 관계 추론
        if _EXTEND_IMPOSSIBLE_RE.search(text):
            for m in _VISA_CODE_RE.finditer(text):
                triples.append(Triple(
                    subject_id="건강보험미납",
                    predicate="BLOCKS",
                    object_id=f"{m.group(1)}_연장",
                    block_reason="건강보험 미납 시 비자 연장 불가",
                    confidence=1.0,
                    source=chunk.source_file,
                    source_page=chunk.source_page,
                ))

        return triples


class LLMExtractor:
    """OpenAI API 기반 구조화 엔티티·관계 추출기."""

    def __init__(self) -> None:
        # 지연 임포트: KB 구축 시에만 OpenAI 클라이언트 사용
        self._client = None

    def _get_client(self):
        if self._client is None:
            from graph_rag.llm.openai_client import OpenAIKBClient
            self._client = OpenAIKBClient()
        return self._client

    def extract(self, chunk: ChunkNode) -> Tuple[List[EntityNode], List[Triple]]:
        """
        Chunk에서 엔티티와 관계를 JSON 형식으로 추출한다.
        LLM 오류 시 빈 목록을 반환한다 (전체 파이프라인 중단 방지).
        """
        try:
            client = self._get_client()
            result = client.extract_entities_and_relations(chunk.text, chunk.source_file)
        except Exception as exc:
            logger.error("LLM 추출 실패 (chunk=%s): %s", chunk.id, exc)
            return [], []

        entities = self._parse_entities(result.get("entities", []), chunk)
        triples = self._parse_triples(result.get("relations", []), chunk)
        return entities, triples

    def _parse_entities(self, raw: list, chunk: ChunkNode) -> List[EntityNode]:
        entities = []
        for item in raw:
            try:
                entities.append(EntityNode(
                    id=item["id"],
                    name=item.get("name", item["id"]),
                    domain=item.get("domain", "visa"),
                    summary=item.get("summary", ""),
                    confidence=float(item.get("confidence", 0.8)),
                    source=chunk.source_file,
                ))
            except (KeyError, ValueError) as exc:
                logger.warning("엔티티 파싱 실패: %s (%s)", item, exc)
        return entities

    def _parse_triples(self, raw: list, chunk: ChunkNode) -> List[Triple]:
        triples = []
        for item in raw:
            predicate = item.get("predicate", "")
            if predicate not in ALLOWED_PREDICATES:
                logger.warning("허용되지 않은 predicate 무시: %s", predicate)
                continue
            try:
                triples.append(Triple(
                    subject_id=item["subject_id"],
                    predicate=predicate,
                    object_id=item["object_id"],
                    condition=item.get("condition", ""),
                    confidence=float(item.get("confidence", 0.8)),
                    source=chunk.source_file,
                    source_page=chunk.source_page,
                ))
            except (KeyError, ValueError) as exc:
                logger.warning("트리플 파싱 실패: %s (%s)", item, exc)
        return triples


class HybridExtractor:
    """규칙 기반 + LLM 혼합 추출기 (파이프라인의 4단계)."""

    def __init__(self, use_llm: bool = True) -> None:
        self._rule = RuleBasedExtractor()
        self._llm = LLMExtractor() if use_llm else None

    def extract_all(
        self, chunks: List[ChunkNode]
    ) -> Tuple[List[EntityNode], List[Triple], List[Tuple[str, str]]]:
        """
        Returns:
            entities: 추출된 EntityNode 목록
            triples: 추출된 Triple 목록
            chunk_links: (entity_id, chunk_id) 연결 목록
        """
        all_entities: List[EntityNode] = []
        all_triples: List[Triple] = []
        chunk_links: List[Tuple[str, str]] = []

        for chunk in chunks:
            # 규칙 기반 추출
            rule_entities = self._rule.extract_entities(chunk)
            rule_triples = self._rule.extract_triples(chunk)

            # 규칙 기반에서 아무것도 못 잡은 청크만 LLM에 넘긴다.
            # 이렇게 하면 API 호출 수와 비용을 크게 줄일 수 있다.
            llm_entities: List[EntityNode] = []
            llm_triples: List[Triple] = []
            if self._llm and not rule_entities and not rule_triples:
                llm_entities, llm_triples = self._llm.extract(chunk)

            # 병합
            entities = rule_entities + llm_entities
            triples = rule_triples + llm_triples

            all_entities.extend(entities)
            all_triples.extend(triples)

            # chunk 연결 정보
            for ent in entities:
                chunk_links.append((ent.id, chunk.id))

        return all_entities, all_triples, chunk_links
