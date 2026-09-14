"""
yhs/ingest/pipeline/extractor.py

역할:
- Chunk 목록에서 엔티티와 관계를 추출한다.
- 규칙 기반: 비자코드, 체류기간, 기관명 → confidence 1.0
- LLM 기반: OpenAI API를 통한 구조화 JSON 추출 → confidence 0.7~0.9
- 허용 predicate를 7개로 고정하여 스키마 밖 관계 생성을 방지한다.
"""

from __future__ import annotations

import logging
import re

from yhs.core.config import ALLOWED_PREDICATES, KNOWN_INSTITUTIONS
from yhs.ingest.stats import STATS
from yhs.ingest.validation import validate
from yhs.schema.types import ChunkNode, EntityNode, Triple

logger = logging.getLogger(__name__)

# ─── 규칙 기반 패턴 ───────────────────────────────────────────────────────────
_VISA_CODE_RE = re.compile(r"\b([A-Z]-\d+(?:-\d+)?)\b")
_DURATION_RE = re.compile(r"(\d+년|\d+개월|\d+일)")
_EXTEND_POSSIBLE_RE = re.compile(r"연장\s*가능")
_EXTEND_IMPOSSIBLE_RE = re.compile(r"연장\s*불가")
_SECTION_HEADER_RE = re.compile(r"(유형\d+|\d+단계|Part\s*\d+)", re.IGNORECASE)


# ── JSON 키 별칭 ─────────────────────────────────────────────────────────────
# 로컬 모델은 스키마를 100% 지키지 못한다. 의미가 같은 키는 받아 준다.
# (예전에는 object_id 대신 object 로 왔다는 이유만으로 관계를 통째로 버렸다)
_ID_KEYS = ("id", "entity_id", "identifier")
_NAME_KEYS = ("name", "label", "title", "entity", "id")
_SUBJECT_KEYS = ("subject_id", "subject", "source_id", "source", "from", "head")
_OBJECT_KEYS = ("object_id", "object", "target_id", "target", "to", "tail")
_PREDICATE_KEYS = ("predicate", "relation", "rel", "type", "relation_type")


def _pick(item: dict, keys: tuple[str, ...]):
    """별칭 중 처음으로 값이 있는 키를 돌려준다."""
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return v
    return None


# ── predicate 정규화 ─────────────────────────────────────────────────────────
# 같은 뜻을 다른 이름으로 내놓는 경우를 표준 술어로 모아 준다.
# 허용 목록에 없다고 바로 버리면 의미 있는 관계가 사라진다.
_PREDICATE_ALIASES = {
    "NEXT_STEP": "PRECEDES",
    "PRECEDED_BY": "FOLLOWED_BY",
    "ENABLES_SHORTCUT": "ENABLES",
    "ENABLED_BY": "ENABLES",
    "REQUIRED_FOR": "REQUIRES",
    "NEEDS": "REQUIRES",
    "REQUIRE": "REQUIRES",
    "DEPENDS_ON": "REQUIRES",
    "PREVENTS": "BLOCKS",
    "BLOCKED_BY": "BLOCKS",
    "CONDITION": "HAS_CONDITION",
    "CONDITIONAL_ON": "HAS_CONDITION",
    "EXCEPTION": "HAS_EXCEPTION",
    "EXCEPT": "HAS_EXCEPTION",
    "APPLIES": "APPLIES_TO",
    "APPLICABLE_TO": "APPLIES_TO",
    "VALID_FOR": "APPLIES_TO",
    "AVAILABLE_TO": "APPLIES_TO",
    "ISSUED_FOR": "ISSUED_TO",
    "SUBMIT_TO": "SUBMITTED_TO",
    "FOLLOWS": "FOLLOWED_BY",
}


def normalize_predicate(raw: str) -> str | None:
    """LLM 이 준 술어를 표준 술어로 바꾼다. 매핑도 허용 목록도 없으면 None."""
    if not raw:
        return None
    p = raw.strip().upper().replace(" ", "_").replace("-", "_")
    p = _PREDICATE_ALIASES.get(p, p)
    return p if p in ALLOWED_PREDICATES else None


def _dedupe_entities(entities: list[EntityNode]) -> list[EntityNode]:
    """같은 id 의 엔티티를 하나로 합친다.

    규칙 기반(confidence 1.0)과 LLM(0.7~0.9)이 같은 개념을 잡을 수 있다.
    그때는 confidence 가 높은 쪽을 남기되, 비어 있는 필드는 다른 쪽에서
    채운다. 규칙 기반은 type 을 모르고 LLM 은 type 을 아는 식이라
    한쪽만 남기면 정보가 준다.
    """
    best: dict[str, EntityNode] = {}
    for e in entities:
        key = (e.id or e.name or "").strip()
        if not key:
            continue
        cur = best.get(key)
        if cur is None:
            best[key] = e
            continue
        winner, loser = (cur, e) if cur.confidence >= e.confidence else (e, cur)
        # 비어 있는 필드를 진 쪽에서 보충한다.
        if not winner.type and loser.type:
            winner.type = loser.type
        if not winner.summary and loser.summary:
            winner.summary = loser.summary
        best[key] = winner
    return list(best.values())


class RuleBasedExtractor:
    """정규식 기반 엔티티 추출기 (confidence = 1.0)."""

    def extract_entities(self, chunk: ChunkNode) -> list[EntityNode]:
        entities: list[EntityNode] = []
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

    def extract_triples(self, chunk: ChunkNode) -> list[Triple]:
        """규칙 기반 관계 추출."""
        triples: list[Triple] = []
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
            import os
            provider = os.getenv("LLM_PROVIDER", "ollama").lower()
            if provider == "openai":
                from yhs.ingest.llm.openai_client import OpenAIKBClient
                self._client = OpenAIKBClient()
            elif provider == "exaone":
                from yhs.ingest.llm.exaone_kb_client import ExaoneKBClient
                self._client = ExaoneKBClient()
            elif provider == "gemini":
                from yhs.ingest.llm.gemini_client import GeminiKBClient
                self._client = GeminiKBClient()
            else:
                # 기본값: Ollama
                from yhs.ingest.llm.ollama_kb_client import OllamaKBClient
                self._client = OllamaKBClient()
        return self._client

    def extract(self, chunk: ChunkNode) -> tuple[list[EntityNode], list[Triple]]:
        """
        Chunk에서 엔티티와 관계를 JSON 형식으로 추출한다.
        LLM 오류 시 빈 목록을 반환한다 (전체 파이프라인 중단 방지).

        실패는 조용히 넘기지 않고 STATS 에 누적한다. 예전에는 LLM 로딩이
        실패해도 인제스트가 정상 종료해서, 관계만 0건인 상태를 "그래프가
        빈약하다"로 오해하기 쉬웠다.
        """
        try:
            client = self._get_client()
            result = client.extract_entities_and_relations(chunk.text, chunk.source_file)
        except Exception as exc:
            logger.error("LLM 추출 실패 (chunk=%s): %s", chunk.id, exc)
            STATS.llm_failed_chunks += 1
            STATS.llm_error_kinds[type(exc).__name__] += 1
            return [], []

        STATS.llm_success_chunks += 1
        ents, tris = self._parse_and_validate(result, chunk)

        # 관계가 하나도 못 살아남았는데 원래는 있었다면 한 번 더 시도한다.
        # 로컬 모델은 같은 입력에도 출력이 흔들려서, 재시도로 규칙을
        # 지킨 출력이 나오는 경우가 있다. 한 번만 한다 — 무한정 돌리면
        # 인제스트 시간이 감당이 안 된다.
        raw_rel_count = len(result.get("relations", []) or [])
        if raw_rel_count and not tris:
            STATS.chunk_retried += 1
            logger.info("관계가 모두 폐기되어 재시도 (chunk=%s)", chunk.id)
            try:
                retry = client.extract_entities_and_relations(
                    chunk.text, chunk.source_file
                )
            except Exception as exc:
                logger.warning("재시도 실패 (chunk=%s): %s", chunk.id, exc)
            else:
                r_ents, r_tris = self._parse_and_validate(retry, chunk)
                if r_tris:
                    STATS.retry_succeeded += 1
                    return r_ents, r_tris

        return ents, tris

    def _parse_and_validate(
        self, result: dict, chunk: ChunkNode
    ) -> tuple[list[EntityNode], list[Triple]]:
        """파싱 → 검증. json-repair 로 복구한 응답도 반드시 이 경로를 탄다."""
        entities = self._parse_entities(result.get("entities", []), chunk)
        triples = self._parse_triples(result.get("relations", []), chunk)
        # 프롬프트가 규칙을 어겨도 여기서 막는다.
        # (설명성 문단의 가짜 절차 관계, 타입 불일치, endpoint 누락 등)
        return validate(entities, triples, result.get("chunk_type", ""))

    def _parse_entities(self, raw: list, chunk: ChunkNode) -> list[EntityNode]:
        entities = []
        for item in raw:
            if not isinstance(item, dict):
                STATS.entity_parse_failed += 1
                STATS.entity_fail_reasons["dict 아님"] += 1
                continue
            name = _pick(item, _NAME_KEYS)
            ident = _pick(item, _ID_KEYS) or name
            if not ident:
                STATS.entity_parse_failed += 1
                STATS.entity_fail_reasons["id/name 둘 다 없음"] += 1
                logger.warning("엔티티 파싱 실패(식별자 없음): %s", item)
                continue
            try:
                entities.append(EntityNode(
                    id=str(ident),
                    name=str(name or ident),
                    type=str(item.get("type", "") or ""),
                    domain=item.get("domain", "visa"),
                    summary=item.get("summary", ""),
                    confidence=float(item.get("confidence", 0.8)),
                    source=chunk.source_file,
                ))
                STATS.parsed_entities += 1
            except (TypeError, ValueError) as exc:
                STATS.entity_parse_failed += 1
                STATS.entity_fail_reasons[type(exc).__name__] += 1
                logger.warning("엔티티 파싱 실패: %s (%s)", item, exc)
        return entities

    def _parse_triples(self, raw: list, chunk: ChunkNode) -> list[Triple]:
        triples = []
        for item in raw:
            if not isinstance(item, dict):
                STATS.relation_parse_failed += 1
                STATS.relation_fail_reasons["dict 아님"] += 1
                continue

            # 키 이름이 조금 달라도 버리지 않는다.
            # 로컬 모델은 subject_id 를 subject 로, object_id 를 object 로
            # 내는 일이 잦은데, 예전에는 KeyError 로 관계를 통째로 버렸다.
            subject = _pick(item, _SUBJECT_KEYS)
            obj = _pick(item, _OBJECT_KEYS)
            raw_pred = str(_pick(item, _PREDICATE_KEYS) or "").strip()
            predicate = normalize_predicate(raw_pred)

            if not subject or not obj:
                STATS.relation_parse_failed += 1
                STATS.relation_fail_reasons["subject/object 없음"] += 1
                logger.warning("트리플 파싱 실패(주어/목적어 없음): %s", item)
                continue

            if predicate is None:
                # 허용 목록 밖 predicate. 버리되 무엇이 얼마나 버려지는지 남긴다.
                STATS.predicate_rejected += 1
                STATS.rejected_predicates[raw_pred or "(비어 있음)"] += 1
                logger.info("허용되지 않은 predicate 폐기: %r (%s → %s)",
                            raw_pred, subject, obj)
                continue

            try:
                triples.append(Triple(
                    subject_id=str(subject),
                    predicate=predicate,
                    object_id=str(obj),
                    condition=item.get("condition", ""),
                    evidence=str(item.get("evidence", "") or "").strip(),
                    confidence=float(item.get("confidence", 0.8)),
                    source=chunk.source_file,
                    source_page=chunk.source_page,
                ))
                STATS.parsed_relations += 1
                STATS.predicate_seen[predicate] += 1
            except (TypeError, ValueError) as exc:
                STATS.relation_parse_failed += 1
                STATS.relation_fail_reasons[type(exc).__name__] += 1
                logger.warning("트리플 파싱 실패: %s (%s)", item, exc)
        return triples


class HybridExtractor:
    """규칙 기반 + LLM 혼합 추출기 (파이프라인의 4단계)."""

    def __init__(self, use_llm: bool = True) -> None:
        self._rule = RuleBasedExtractor()
        self._llm = LLMExtractor() if use_llm else None

    def extract_all(
        self, chunks: list[ChunkNode]
    ) -> tuple[list[EntityNode], list[Triple], list[tuple[str, str]]]:
        """
        Returns:
            entities: 추출된 EntityNode 목록
            triples: 추출된 Triple 목록
            chunk_links: (entity_id, chunk_id) 연결 목록
        """
        all_entities: list[EntityNode] = []
        all_triples: list[Triple] = []
        chunk_links: list[tuple[str, str]] = []

        for chunk in chunks:
            # 규칙 기반: 확실한 것만 잡는 "보장용" (비자코드·기관명, confidence 1.0)
            rule_entities = self._rule.extract_entities(chunk)
            rule_triples = self._rule.extract_triples(chunk)

            # LLM: 절차·서류·조건 같은 나머지를 채우는 "확장용"
            llm_entities: list[EntityNode] = []
            llm_triples: list[Triple] = []
            if self._llm:
                llm_entities, llm_triples = self._llm.extract(chunk)

            # ── 병합 ─────────────────────────────────────────────────────
            # 예전에는 규칙이 뭐라도 잡으면 LLM 엔티티를 전부 버렸다.
            # 규칙이 잡는 건 비자코드 정규식과 기관명 8개뿐이라, 비자코드가
            # 하나만 있어도 그 청크의 '체류기간연장허가', '외국인등록증' 같은
            # PROCEDURE/DOCUMENT 후보가 통째로 사라졌다. 게다가 LLM 트리플은
            # 그대로 남아서, 그 트리플의 주어·목적어가 존재하지 않는 엔티티를
            # 가리키게 되고 적재 단계의 MATCH 에서 조용히 유실됐다.
            # (실측: 표본 3청크에서 엔티티 20/20 폐기, 관계 34/34 유실)
            #
            # 이제 둘을 합치고 id 기준으로 중복만 제거한다. 같은 id 면
            # confidence 가 높은 쪽(=규칙 기반)을 남긴다.
            entities = _dedupe_entities(rule_entities + llm_entities)
            triples = rule_triples + llm_triples

            STATS.rule_entities += len(rule_entities)

            all_entities.extend(entities)
            all_triples.extend(triples)

            # chunk 연결 정보
            for ent in entities:
                chunk_links.append((ent.id, chunk.id))

        return all_entities, all_triples, chunk_links
