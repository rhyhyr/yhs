"""
agent/retrieval/linker.py

역할: 사용자 질문에서 그래프의 Entity 노드를 찾는 Topic Entity 링킹.
      질문 의도를 먼저 분류한 뒤, 의도 앵커 + 임베딩 매칭으로 Entity를 찾는다.

흐름:
  1. LLM 정규화 (캐시, Ollama 없으면 원문 사용)
  2. 의도 분류 → 앵커 추출
  3. aliases 매칭 (정규화 질문 + 앵커)
  4. 임베딩 유사도 매칭 (name+aliases+summary 결합 텍스트 기준)
  5. 결과: {entity_ids, intents, anchors}
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np

from graph_rag.config import ALIASES_MAP, ENTITY_LINK_COSINE_THRESHOLD, ENTITY_LINK_TOP_K
from graph_rag.db.graph_store import GraphStore
from graph_rag.embedding.embedder import Embedder

logger = logging.getLogger(__name__)

# ─── 의도 분류 상수 ────────────────────────────────────────────────────────────
# 질문에 이 키워드가 포함되면 해당 의도로 분류한다 (소문자 비교)
INTENT_KEYWORDS: dict[str, list[str]] = {
    "visa": [
        "비자", "체류", "d-2", "d-4", "f-2", "f-5", "e-7",
        "연장", "전환", "체류자격", "비자연장", "체류기간",
        "사증", "전자사증", "입국", "입국심사", "출국",
    ],
    "arc": [
        "외국인등록", "외국인등록증", "arc", "등록증", "외국인 등록",
        "외국인등록번호", "등록번호",
    ],
    "health_insurance": [
        "건강보험", "의료보험", "보험 가입", "보험료", "건강보험료", "nhis",
    ],
    "academic": [
        "학사일정", "수강신청", "등록금", "휴학", "복학", "학기", "졸업", "성적",
        "시험", "중간시험", "기말시험", "출결", "전자출결", "강의", "수업",
        "장학금", "학점",
    ],
    "dormitory": [
        "기숙사", "생활관", "한림생활관", "기숙", "호실", "편의시설", "입사",
        "기숙사비", "룸",
    ],
    "life_admin": [
        "출입국", "주소변경", "주소 변경", "취업허가",
        "시간제취업", "시간제 취업", "시간제",
        "은행 계좌", "장학금", "아르바이트", "픽업", "신입생 픽업",
        "캠퍼스", "특성화",
    ],
}

# 의도별로 그래프·벡터 검색에 유리한 앵커 표현
INTENT_ANCHORS: dict[str, list[str]] = {
    "visa": ["비자 연장", "체류기간 연장", "D-2", "D-4", "비자 전환", "체류자격 변경", "사증", "입국심사"],
    "arc": ["외국인등록증", "ARC", "외국인등록", "외국인 등록증", "외국인등록번호"],
    "health_insurance": ["건강보험", "건강보험 가입", "건강보험 납부", "의료보험"],
    "academic": ["학사일정", "수강신청", "등록금", "휴학", "복학", "중간시험", "기말시험", "전자출결", "학점"],
    "dormitory": ["기숙사", "생활관", "한림생활관", "기숙사비", "호실"],
    "life_admin": ["출입국관리사무소", "주소 변경", "취업 허가", "시간제 취업", "픽업 서비스", "캠퍼스"],
}


def _classify_intent(question: str) -> list[str]:
    """질문에서 매칭되는 의도 버킷 목록을 반환한다."""
    q = question.lower()
    return [intent for intent, kws in INTENT_KEYWORDS.items() if any(kw in q for kw in kws)]


def _extract_anchors(intents: list[str]) -> list[str]:
    """의도 목록에서 중복 없이 앵커 표현을 모은다."""
    seen: set[str] = set()
    anchors: list[str] = []
    for intent in intents:
        for anchor in INTENT_ANCHORS.get(intent, []):
            if anchor not in seen:
                anchors.append(anchor)
                seen.add(anchor)
    return anchors


class EntityLinker:
    """의도 분류 + 3단계 Entity 링킹."""

    def __init__(self, store: GraphStore, embedder: Embedder, ollama_client=None) -> None:
        self._store = store
        self._embedder = embedder
        self._ollama_client = ollama_client
        self._entity_cache: list[dict] | None = None
        self._entity_texts: list[str] = []          # name + aliases + summary 결합
        self._entity_embeddings: np.ndarray | None = None
        self._entity_ids: list[str] = []
        self._normalized_cache: dict[str, str] = {}

    def _load_entity_cache(self) -> None:
        if self._entity_cache is not None:
            return
        self._entity_cache = self._store.get_all_entities_summary()
        self._entity_ids = [e["id"] for e in self._entity_cache]

        # name + aliases + summary를 결합해 더 풍부한 임베딩 텍스트를 만든다
        texts = []
        for e in self._entity_cache:
            name = e.get("name", "")
            aliases = e.get("aliases") or []
            summary = e.get("summary", "")
            combined = " ".join(filter(None, [name, " ".join(aliases), summary]))
            texts.append(combined if combined.strip() else name)
        self._entity_texts = texts

        if texts:
            self._entity_embeddings = self._embedder.encode(texts)
        else:
            self._entity_embeddings = np.zeros((0, 1024), dtype=np.float32)

    def invalidate_cache(self) -> None:
        self._entity_cache = None
        self._entity_embeddings = None
        self._entity_ids = []
        self._entity_texts = []
        self._normalized_cache.clear()

    # ── Step 0: LLM 정규화 (캐시 적용) ──────────────────────────────────────
    def _step0_llm_normalize(self, question: str) -> str:
        cached = self._normalized_cache.get(question)
        if cached is not None:
            return cached

        if self._ollama_client is None:
            self._normalized_cache[question] = question
            return question

        try:
            normalized = self._ollama_client.normalize_question(question)
            result = normalized if normalized else question
            self._normalized_cache[question] = result
            return result
        except Exception as exc:
            logger.warning("LLM 정규화 실패, 원본 질문 사용: %s", exc)
            self._normalized_cache[question] = question
            return question

    # ── Step 1: Alias 매칭 ───────────────────────────────────────────────────
    def _step1_aliases_match(self, keyword: str) -> List[str]:
        """ALIASES_MAP + entity name/alias 비교로 매칭 ID를 반환한다."""
        kw_lower = keyword.lower().strip()
        matched: List[str] = []

        for alias, standard_id in ALIASES_MAP.items():
            if alias.lower() in kw_lower or kw_lower in alias.lower():
                if standard_id not in matched:
                    matched.append(standard_id)

        self._load_entity_cache()
        for entity in self._entity_cache or []:
            eid = entity["id"]
            name = entity.get("name", "")
            aliases = entity.get("aliases") or []

            check_terms = [name] + aliases + [eid]
            for term in check_terms:
                if term and (term.lower() in kw_lower or kw_lower in term.lower()):
                    if eid not in matched:
                        matched.append(eid)
                    break

        return matched

    # ── Step 2: 임베딩 유사도 매칭 ──────────────────────────────────────────
    def _step2_embedding_match(self, question: str) -> List[str]:
        self._load_entity_cache()
        if self._entity_embeddings is None or len(self._entity_embeddings) == 0:
            return []

        q_emb = self._embedder.encode_single(question)
        sims = self._embedder.cosine_similarity(q_emb, self._entity_embeddings)

        top_indices = np.argsort(sims)[::-1][:ENTITY_LINK_TOP_K]
        return [
            self._entity_ids[idx]
            for idx in top_indices
            if sims[idx] >= ENTITY_LINK_COSINE_THRESHOLD
        ]

    # ── 메인 링킹 ────────────────────────────────────────────────────────────
    def link(self, question: str) -> dict:
        """
        질문을 분석하여 관련 Entity ID 목록과 의도 정보를 반환한다.

        반환값:
            {
                "entity_ids": List[str],   # 그래프 탐색 시작점
                "intents": List[str],      # 분류된 의도 버킷
                "anchors": List[str],      # 벡터 검색 키워드 강화용 앵커
            }
        """
        normalized = self._step0_llm_normalize(question)
        logger.debug("LLM 정규화: '%s' → '%s'", question, normalized)

        # 의도 분류는 원문 질문 기준으로 (정규화 전에 더 정확할 수 있음)
        intents = _classify_intent(question)
        anchors = _extract_anchors(intents)
        logger.debug("의도 분류: %s, 앵커: %s", intents, anchors)

        # Step 1: 정규화 질문 + 앵커 각각으로 alias 매칭
        step1_ids: List[str] = self._step1_aliases_match(normalized)
        for anchor in anchors:
            for eid in self._step1_aliases_match(anchor):
                if eid not in step1_ids:
                    step1_ids.append(eid)
        logger.debug("aliases 매칭: %s", step1_ids)

        # Step 2: 임베딩 유사도 매칭
        step2_ids = self._step2_embedding_match(normalized)
        logger.debug("임베딩 유사도 매칭: %s", step2_ids)

        # 중복 제거 (step1 우선)
        seen: set[str] = set()
        all_ids: List[str] = []
        for eid in step1_ids + step2_ids:
            if eid not in seen:
                all_ids.append(eid)
                seen.add(eid)

        logger.info("링킹 결과: %d개 Entity %s, 의도: %s", len(all_ids), all_ids, intents)
        return {
            "entity_ids": all_ids,
            "intents": intents,
            "anchors": anchors,
        }
