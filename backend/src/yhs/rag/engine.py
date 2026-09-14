"""
yhs/rag/engine.py

역할:
- 검색 오케스트레이터. 그래프 탐색과 벡터 검색을 함께 실행하고 재랭크한다.

흐름:
  1. EntityLinker.link() → entity_ids + intents + anchors
  2. 그래프 탐색 (entity_ids → edges + graph_chunks)
  3. 벡터 검색 (question + anchors → vector_chunks)
  4. _merge_and_rerank(): 양쪽 후보를 합산 스코어로 재정렬
  5. 결과가 없으면 "모름" 응답 반환

- 신선도 경고(6개월 이상 경과 문서)를 자동 삽입한다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from yhs.core.config import (
    DEFAULT_HOP_DEPTH,
    DISCLAIMER_TEMPLATE,
    DOC_STALENESS_MONTHS,
    TOP_K_GRAPH_DEFAULT,
)
from yhs.core.settings import load_config
from yhs.infra.embedder import Embedder
from yhs.infra.graph_store import GraphStore
from yhs.rag.retrieval.graph_retriever import DDEGraphRetriever
from yhs.rag.retrieval.linker import EntityLinker
from yhs.rag.retrieval.vector_retriever import VectorRetriever
from yhs.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

# ── 튜닝 파라미터 ────────────────────────────────────────────────────────────
# 값은 backend/config/retrieval.yaml 에 있다. 코드에 숫자를 박지 말 것 —
# 가중치는 Optuna 스윕(experiments/weight_sweep_optuna.py)의 결과물이라
# 재현성을 위해 버전 관리 대상이어야 한다.
_cfg = load_config("retrieval")

_CANDIDATE_TOP_K = _cfg["rerank"]["candidate_top_k"]
_FINAL_TOP_K = _cfg["rerank"]["final_top_k"]
_MIN_CHUNK_SCORE = _cfg["rerank"]["min_chunk_score"]

# 병합 스코어 가중치
_W_BASE = _cfg["weights"]["base"]        # 출처 기반 점수 (그래프 홉 점수 or 벡터 cosine)
_W_KW = _cfg["weights"]["keyword"]       # 키워드/앵커 겹침
_W_REC = _cfg["weights"]["recency"]      # 문서 최신성

# 그래프 연결 청크의 베이스 스코어 (직접 링크 = 높은 신뢰도)
_GRAPH_BASE_SCORE = _cfg["base_scores"]["graph"]
# 소스 라우팅된 청크의 보장 베이스 스코어 (그래프 청크보다 높아야 최종 top-k 진입)
_ROUTED_BASE_SCORE = _cfg["base_scores"]["routed"]

_QUESTION_FIT_THRESHOLD = _cfg["question_fit_threshold"]

# 헤더/메타 청크 감지 패턴 (URL/출처기관/수집일만 있는 청크에 페널티)
_HEADER_MARKERS = tuple(_cfg["header_markers"])

# 키워드 → 소스파일 라우팅 (backend/config/routing.yaml)
# 엔티티 링킹 실패 보완: 질문에 키워드가 있으면 해당 파일을 강제 포함한다.
_SOURCE_ROUTING: dict[str, list[str]] = load_config("routing")["source_routing"]


def _is_stale(doc_version: str, months: int = DOC_STALENESS_MONTHS) -> bool:
    """doc_version(YYYY.MM 형식)이 기준 개월 이상 경과했으면 True."""
    if not doc_version:
        return False
    try:
        parts = doc_version.replace("-", ".").split(".")
        year, month = int(parts[0]), int(parts[1])
        doc_date = datetime(year, month, 1)
        return datetime.now() - doc_date > timedelta(days=30 * months)
    except (ValueError, IndexError):
        return False


def _recency_score(doc_version: str) -> float:
    """문서 최신성 점수 (0개월 → 1.0, 24개월+ → 0.0)."""
    if not doc_version:
        return 0.5
    try:
        parts = doc_version.replace("-", ".").split(".")
        year, month = int(parts[0]), int(parts[1])
        doc_date = datetime(year, month, 1)
        months_old = max(0, (datetime.now() - doc_date).days / 30)
        return max(0.0, 1.0 - months_old / 24.0)
    except (ValueError, IndexError):
        return 0.5


def _build_disclaimer(source_file: str, doc_version: str) -> str:
    return DISCLAIMER_TEMPLATE.format(source_file=source_file, doc_version=doc_version)


def _keyword_overlap(text: str, question: str, anchors: list[str]) -> float:
    """앵커 히트율 + 질문-텍스트 단어 겹침을 결합한 키워드 점수."""
    t_lower = text.lower()
    q_lower = question.lower()

    if anchors:
        anchor_hits = sum(1 for a in anchors if a.lower() in t_lower)
        anchor_score = min(anchor_hits / len(anchors), 1.0)
    else:
        anchor_score = 0.0

    q_terms = {t for t in q_lower.split() if len(t) > 1}
    t_terms = {t for t in t_lower.split() if len(t) > 1}
    term_overlap = len(q_terms & t_terms) / max(len(q_terms), 1) if q_terms else 0.0

    return 0.6 * anchor_score + 0.4 * term_overlap


def _question_chunk_fit(chunks: list[dict], question: str, anchors: list[str]) -> float:
    """질문과 검색 청크 간 정합도(최대값) 계산."""
    if not chunks:
        return 0.0
    return max(
        _keyword_overlap(c.get("text", ""), question, anchors)
        for c in chunks
    )


def _is_header_chunk(text: str) -> bool:
    """URL/출처/날짜만 있는 메타데이터 청크 여부 감지."""
    if not text or len(text.strip()) < 10:
        return True
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) <= 4:
        marker_lines = sum(1 for ln in lines if any(m in ln for m in _HEADER_MARKERS))
        if marker_lines >= len(lines) - 1:
            return True
    return False


class RetrievalEngine:
    """그래프+벡터 병합 검색 오케스트레이터."""

    def __init__(self, store: GraphStore, embedder: Embedder, ollama_client=None) -> None:
        self._store = store
        self._embedder = embedder
        self._ollama_client = ollama_client
        self._linker = EntityLinker(store, embedder, ollama_client=ollama_client)
        self._graph_retriever = DDEGraphRetriever(store)
        self._vector_retriever = VectorRetriever(store, embedder)

    def invalidate_caches(self) -> None:
        """새 데이터 인제스트 후 내부 캐시를 모두 무효화한다."""
        self._linker.invalidate_cache()
        self._vector_retriever.invalidate_index()

    def _fetch_source_routed_chunks(self, question: str) -> list[dict]:
        """질문에 라우팅 키워드가 있으면 해당 소스 파일 청크를 직접 가져온다."""
        q_lower = question.lower()
        target_files: list[str] = []
        for keyword, files in _SOURCE_ROUTING.items():
            if keyword.lower() in q_lower:
                for f in files:
                    if f not in target_files:
                        target_files.append(f)

        if not target_files:
            return []

        all_chunks = self._vector_retriever._get_all_chunks()
        routed: list[dict] = []
        for chunk in all_chunks:
            if chunk.get("source_file") in target_files:
                routed.append({**chunk, "_from": "routed"})

        logger.info(
            "소스 라우팅: 키워드 감지 → %s → %d개 청크 추가",
            target_files, len(routed),
        )
        return routed

    # ── 주 검색 ──────────────────────────────────────────────────────────────
    def retrieve(
        self,
        question: str,
        hop_depth: int = DEFAULT_HOP_DEPTH,
        top_k: int = TOP_K_GRAPH_DEFAULT,
    ) -> RetrievalResult:
        """질문에 대한 검색 결과를 반환한다."""
        link_result = self._linker.link(question)
        entity_ids: list[str] = link_result["entity_ids"]
        anchors: list[str] = link_result["anchors"]
        intents: list[str] = link_result["intents"]

        # ── 그래프 탐색 ───────────────────────────────────────────────────
        triples: list = []
        graph_chunks: list = []
        if entity_ids:
            triples, graph_chunks = self._graph_retriever.retrieve(
                entity_ids, hop_depth=hop_depth, top_k=top_k
            )

        # ── 벡터 검색 ─────────────────────────────────────────────────────
        # 멀티홉/복합 질문이거나 그래프 결과가 부족할 때는 반드시 실행.
        # 단순 질문에서 그래프가 충분하면 벡터 생략으로 속도 개선.
        is_multi_intent = len(intents) >= 2
        needs_vector = True  # 그래프 단독으로는 정합도 부족 → 항상 벡터 병행

        vector_chunks: list = []
        if needs_vector:
            vector_chunks = self._vector_retriever.search(
                question,
                top_k=_CANDIDATE_TOP_K,
                keywords=anchors,
            )
            logger.info(
                "벡터 검색 실행 (그래프=%d청크, multi_intent=%s): %d개 반환",
                len(graph_chunks), is_multi_intent, len(vector_chunks),
            )

        # ── 소스 라우팅 (엔티티 링킹 보완) ─────────────────────────────────
        routed_chunks = self._fetch_source_routed_chunks(question)
        has_routing = bool(routed_chunks)

        # ── 병합 재랭크 ───────────────────────────────────────────────────
        merged = self._merge_and_rerank(
            graph_chunks, vector_chunks, question, anchors,
            routed_chunks=routed_chunks,
        )

        if merged:
            # 소스 라우팅이 적용된 경우 fit 체크 생략 (명시적으로 관련 문서를 선택했으므로)
            if not has_routing:
                fit = _question_chunk_fit(merged, question, anchors)
                if fit < _QUESTION_FIT_THRESHOLD:
                    logger.info(
                        "질문-문서 정합도 미달로 no_answer 처리 (fit=%.3f, threshold=%.2f)",
                        fit,
                        _QUESTION_FIT_THRESHOLD,
                    )
                    return RetrievalResult(
                        triples=[],
                        chunks=[],
                        retrieval_method="no_answer",
                        entity_ids=entity_ids,
                    )

            method = _decide_method(graph_chunks, vector_chunks)
            return self._build_result(triples, merged, method, entity_ids)

        logger.info("검색 결과 없음 → '모름' 응답 반환")
        return RetrievalResult(
            triples=[],
            chunks=[],
            retrieval_method="no_answer",
            entity_ids=entity_ids,
        )

    # ── 병합 재랭크 ──────────────────────────────────────────────────────────
    def _merge_and_rerank(
        self,
        graph_chunks: list,
        vector_chunks: list,
        question: str,
        anchors: list[str],
        top_k: int = _FINAL_TOP_K,
        routed_chunks: list | None = None,
    ) -> list[dict]:
        """그래프 청크와 벡터 청크를 합산 스코어로 병합·재정렬한다."""
        seen: dict[str, dict] = {}

        for chunk in graph_chunks:
            cid = chunk.get("id", "")
            if not cid:
                continue
            kw = _keyword_overlap(chunk.get("text", ""), question, anchors)
            rec = _recency_score(chunk.get("doc_version", ""))
            base = chunk.get("_graph_score") or _GRAPH_BASE_SCORE
            if _is_header_chunk(chunk.get("text", "")):
                base -= 0.18
            final = _W_BASE * base + _W_KW * kw + _W_REC * rec
            seen[cid] = {**chunk, "_score": final, "_from": "graph"}

        for chunk in vector_chunks:
            cid = chunk.get("id", "")
            if not cid:
                continue
            cosine = float(chunk.get("score", 0.0))
            kw = _keyword_overlap(chunk.get("text", ""), question, anchors)
            rec = _recency_score(chunk.get("doc_version", ""))
            if _is_header_chunk(chunk.get("text", "")):
                cosine = max(0.0, cosine - 0.18)
            final = _W_BASE * cosine + _W_KW * kw + _W_REC * rec

            if cid in seen:
                # 같은 청크가 그래프와 벡터 양쪽에서 나오면 더 높은 점수 사용
                seen[cid]["_score"] = max(seen[cid]["_score"], final)
            else:
                seen[cid] = {**chunk, "_score": final, "_from": "vector"}

        # 소스 라우팅 청크: 보장 높은 base score로 항상 풀에 포함
        for chunk in (routed_chunks or []):
            cid = chunk.get("id", "")
            if not cid:
                continue
            kw = _keyword_overlap(chunk.get("text", ""), question, anchors)
            rec = _recency_score(chunk.get("doc_version", ""))
            base = _ROUTED_BASE_SCORE
            if _is_header_chunk(chunk.get("text", "")):
                base -= 0.18
            final = _W_BASE * base + _W_KW * kw + _W_REC * rec

            if cid in seen:
                seen[cid]["_score"] = max(seen[cid]["_score"], final)
                seen[cid]["_from"] = "routed"
            else:
                seen[cid] = {**chunk, "_score": final, "_from": "routed"}

        if not seen:
            return []

        ranked = sorted(seen.values(), key=lambda x: x["_score"], reverse=True)
        ranked = [c for c in ranked if c.get("_score", 0.0) >= _MIN_CHUNK_SCORE]

        if not ranked:
            logger.info(
                "병합 재랭크 결과가 임계값 미달로 비어 있음 (threshold=%.2f)",
                _MIN_CHUNK_SCORE,
            )
            return []

        logger.info(
            "병합 재랭크: 그래프 %d + 벡터 %d → threshold %.2f 통과 %d개, top %d (best_score=%.3f)",
            len(graph_chunks), len(vector_chunks),
            _MIN_CHUNK_SCORE,
            len(ranked),
            min(top_k, len(ranked)),
            ranked[0]["_score"],
        )
        return ranked[:top_k]

    # ── 결과 빌더 ────────────────────────────────────────────────────────────
    def _build_result(
        self,
        triples: list,
        chunks_raw: list,
        method: str,
        entity_ids: list[str],
    ) -> RetrievalResult:
        from yhs.schema.types import ChunkNode

        chunk_nodes: list[ChunkNode] = []
        for c in chunks_raw:
            chunk_nodes.append(ChunkNode(
                id=c.get("id", ""),
                text=c.get("text", ""),
                source_file=c.get("source_file", ""),
                source_page=c.get("source_page", 0),
                section=c.get("section", ""),
                doc_version=c.get("doc_version", ""),
                score=float(c.get("_score", c.get("score", 0.0)) or 0.0),
            ))
        return RetrievalResult(
            triples=triples,
            chunks=chunk_nodes,
            retrieval_method=method,
            entity_ids=entity_ids,
        )

    # ── 프롬프트 컨텍스트 빌더 ──────────────────────────────────────────────
    def build_prompt_context(self, result: RetrievalResult) -> str:
        """검색 결과를 LLM 프롬프트용 컨텍스트 문자열로 변환한다."""
        if result.retrieval_method == "no_answer":
            return ""

        lines: list[str] = []

        if result.triples:
            lines.append("[그래프 트리플]")
            for t in result.triples[:15]:
                lines.append(
                    f"({t.get('src_id', '')}, {t.get('rel_type', '')}, {t.get('dst_id', '')})"
                )
            lines.append("")

        if result.chunks:
            lines.append("[원문]")
            for chunk in result.chunks[:4]:
                # 출처 메타데이터 표시
                loc_parts = []
                if chunk.source_file:
                    loc_parts.append(chunk.source_file)
                if chunk.doc_version:
                    loc_parts.append(chunk.doc_version)
                if chunk.section:
                    loc_parts.append(f"섹션: {chunk.section}")
                if chunk.source_page:
                    loc_parts.append(f"p.{chunk.source_page}")
                if loc_parts:
                    lines.append(f"[{' | '.join(loc_parts)}]")

                lines.append(f"{chunk.text[:700]}")

                if chunk.doc_version and _is_stale(chunk.doc_version):
                    lines.append(_build_disclaimer(chunk.source_file, chunk.doc_version))
                lines.append("")

        sources = sorted({
            f"{c.source_file} ({c.doc_version})"
            for c in result.chunks
            if c.source_file
        })
        if sources:
            lines.append(f"[출처] {', '.join(sources)}")

        return "\n".join(lines)


# ── 유틸 ─────────────────────────────────────────────────────────────────────
def _decide_method(graph_chunks: list, vector_chunks: list) -> str:
    if graph_chunks and vector_chunks:
        return "hybrid"
    if graph_chunks:
        return "graph"
    return "vector"
