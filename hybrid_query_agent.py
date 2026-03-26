# # 1번째 질문이 들어오면:
# 질의 정규화, 오타 보정, 동의어 확장, 법조문 패턴 추출
# 카테고리/청크를 Neo4j에서 하이브리드 검색(벡터+키워드)
# 점수/근거가 충분하면 답변 생성, 부족하면 “DB 근거 부족”으로 답변 거절
# 2번째 질문이 들어와도:
# 1번째 질문 맥락을 거의 사용하지 않고 같은 파이프라인을 새로 실행
# 즉, 기본적으로 멀티턴 문맥 유지보다 “질문 단건 정확 검색”에 최적화됨


from __future__ import annotations

import json
import hashlib
import os
import re
import sys
import time
import urllib.parse
import difflib
from dataclasses import dataclass
from typing import Any, Optional

import google.generativeai as genai
import numpy as np
import requests
from bs4 import BeautifulSoup
from google.api_core import exceptions as gapi_exceptions
from neo4j import GraphDatabase
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agent_runtime import (
    append_latency_log,
    build_answer_prompt,
    detect_language,
    detect_question_type,
    expand_query,
    GateThresholds,
    insufficient_evidence_message,
    normalize_query,
    run_deep_path,
    WebSearchClient,
)

# sentence-transformers / torch 가 없어도 동작
try:
    from sentence_transformers import SentenceTransformer
    _ST_ERROR: Optional[Exception] = None
except Exception as _e:
    SentenceTransformer = None  # type: ignore[assignment,misc]
    _ST_ERROR = _e


def load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.0-flash")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", os.environ.get("NEO4J_USERNAME", "neo4j"))
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

EMBED_MODEL = os.environ.get("EMBED_MODEL", "jhgan/ko-sroberta-multitask")

TOP_CAT = int(os.environ.get("TOP_CAT", "4"))
TOP_SUB = int(os.environ.get("TOP_SUB", "8"))
TOP_CHUNK = int(os.environ.get("TOP_CHUNK", "36"))
FINAL_TOP = int(os.environ.get("FINAL_TOP", "10"))
VEC_WEIGHT = float(os.environ.get("VEC_WEIGHT", "0.62"))
KW_WEIGHT = float(os.environ.get("KW_WEIGHT", "0.38"))
LEXICAL_CAND_LIMIT = int(os.environ.get("LEXICAL_CAND_LIMIT", "500"))

MIN_CHUNKS_FOR_ANSWER = int(os.environ.get("MIN_CHUNKS_FOR_ANSWER", "2"))
MIN_BEST_SCORE = float(os.environ.get("MIN_BEST_SCORE", "0.40"))
SEM_DEDUP_THRESHOLD = float(os.environ.get("SEM_DEDUP_THRESHOLD", "0.95"))
MMR_LAMBDA = float(os.environ.get("MMR_LAMBDA", "0.80"))
ENABLE_LLM_RERANK = os.environ.get("ENABLE_LLM_RERANK", "0") == "1"
LLM_RERANK_CAND = int(os.environ.get("LLM_RERANK_CAND", "12"))
CRAWL_MAX_DOCS = int(os.environ.get("CRAWL_MAX_DOCS", "8"))
ENABLE_CRAWL = False  # DB 정보 부족 시 외부 크롤링은 사용하지 않음
CRAWL_SEARCH_TIMEOUT = int(os.environ.get("CRAWL_SEARCH_TIMEOUT", "5"))
CRAWL_FETCH_TIMEOUT = int(os.environ.get("CRAWL_FETCH_TIMEOUT", "6"))
CRAWL_SLEEP_SEC = float(os.environ.get("CRAWL_SLEEP_SEC", "0.15"))
ENABLE_EXTERNAL_SEARCH = os.environ.get("ENABLE_EXTERNAL_SEARCH", "1") == "1"
LATENCY_LOG_PATH = os.environ.get("LATENCY_LOG_PATH", "logs/latency_log.jsonl")


@dataclass
class CatRec:
    node_id: str
    name: str
    level: int
    keywords: list[str]
    embedding: Optional[np.ndarray]


@dataclass
class ChunkRec:
    chunk_id: str
    text: str
    page: int
    doc_key: str
    embedding: Optional[np.ndarray]


@dataclass
class SourceRef:
    chunk_id: str
    pdf_title: str
    section: str
    page: int
    score: float


@dataclass
class QueryPlan:
    raw_query: str
    normalized_query: str
    embedding_query: str
    bm25_query: str
    keyword_terms: list[str]
    legal_refs: list[str]


class FallbackEmbedder:
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


class HybridQueryAgent:
    _SYNONYM_GROUPS: list[set[str]] = [
        {"신청", "신고", "접수", "청구"},
        {"기한", "기간", "기일", "마감"},
        {"재발급", "재교부", "재발행"},
        {"과태료", "벌칙", "벌금"},
        {"체류", "거주", "체재"},
        {"허가", "승인", "인가"},
    ]

    _TYPO_MAP: dict[str, str] = {
        "신처": "신청",
        "재밝급": "재발급",
        "재발굽": "재발급",
        "과태로": "과태료",
        "가태료": "과태료",
        "기긴": "기한",
        "체루": "체류",
    }

    def __init__(self) -> None:
        if not NEO4J_PASSWORD:
            raise ValueError("NEO4J_PASSWORD is required in .env")

        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.driver.verify_connectivity()
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": "Mozilla/5.0"})
        self.model_name = GEMINI_MODEL
        self.is_fallback_embedder = False

        self.embedder = self._build_embedder()
        self.llm = self._build_model() if GEMINI_API_KEY else None
        # fallback 임베더일 때는 점수가 전반적으로 낮아 임계치를 완화
        self.min_best_score = 0.08 if self.is_fallback_embedder else MIN_BEST_SCORE
        self._domain_terms = sorted({t for g in self._SYNONYM_GROUPS for t in g} | set(self._TYPO_MAP.values()))
        self._gate = GateThresholds.from_env()
        if self.is_fallback_embedder:
            self._gate.min_top_score = 0.08
        self._web_client = WebSearchClient(timeout=5) if ENABLE_EXTERNAL_SEARCH else None

    def close(self) -> None:
        if self._web_client is not None:
            self._web_client.close()
        self.http.close()
        self.driver.close()

    def _build_embedder(self) -> Any:
        if SentenceTransformer is None:
            print(f"[WARN] sentence-transformers unavailable, fallback embedder used: {_ST_ERROR}")
            self.is_fallback_embedder = True
            return FallbackEmbedder()
        try:
            return SentenceTransformer(EMBED_MODEL)
        except Exception as e:
            print(f"[WARN] sentence-transformers init failed, fallback embedder used: {e}")
            self.is_fallback_embedder = True
            return FallbackEmbedder()

    def _build_model(self) -> Optional[genai.GenerativeModel]:
        try:
            genai.configure(api_key=GEMINI_API_KEY)

            preferred = [
                GEMINI_MODEL,
                "gemini-3.0-flash",
                "gemini-3-flash",
                "gemini-flash-latest",
            ]

            models = list(genai.list_models())
            available = {
                m.name.replace("models/", "")
                for m in models
                if "generateContent" in (getattr(m, "supported_generation_methods", []) or [])
            }

            for name in preferred:
                if name in available:
                    self.model_name = name
                    if name != GEMINI_MODEL:
                        print(f"[INFO] Gemini 모델 자동 전환: {GEMINI_MODEL} -> {name}")
                    return genai.GenerativeModel(name)

            if available:
                chosen = sorted(available)[0]
                self.model_name = chosen
                print(f"[INFO] Gemini 모델 자동 선택: {chosen}")
                return genai.GenerativeModel(chosen)

            # 목록 조회는 됐지만 사용 가능한 모델이 없으면 환경값으로 시도
            self.model_name = GEMINI_MODEL
            return genai.GenerativeModel(GEMINI_MODEL)
        except Exception as e:
            print(f"[WARN] Gemini init failed: {e}")
            return None

    def _format_context(self, contexts: list[str]) -> str:
        return "\n\n".join(contexts)

    def _title_from_meta(self, file_path: str, doc_key: str) -> str:
        if file_path:
            base = os.path.splitext(os.path.basename(file_path))[0].strip()
            if base:
                return base
        return f"document-{doc_key[:8]}"

    def _build_source_refs(self, ranked_chunks: list[tuple[ChunkRec, float]], top_n: int) -> list[SourceRef]:
        selected = ranked_chunks[:top_n]
        if not selected:
            return []

        chunk_ids = [ch.chunk_id for ch, _ in selected]
        meta_by_chunk: dict[str, tuple[str, str]] = {}
        with self.driver.session() as s:
            recs = s.run(
                """
                UNWIND $chunk_ids AS cid
                MATCH (ch:Chunk {chunk_id: cid})
                OPTIONAL MATCH (d:Document {doc_key: ch.doc_key})
                OPTIONAL MATCH (ch)-[:BELONGS_TO]->(cat:Category)
                RETURN ch.chunk_id AS chunk_id,
                       coalesce(d.file_path, "") AS file_path,
                       coalesce(cat.name, "관련 조항") AS section,
                       coalesce(ch.doc_key, "") AS doc_key
                """,
                chunk_ids=chunk_ids,
            )
            for r in recs:
                chunk_id = r["chunk_id"]
                title = self._title_from_meta(r["file_path"], r["doc_key"])
                section = (r["section"] or "관련 조항").strip()
                meta_by_chunk[chunk_id] = (title, section)

        out: list[SourceRef] = []
        for ch, score in selected:
            title, section = meta_by_chunk.get(ch.chunk_id, (f"document-{ch.doc_key[:8]}", "관련 조항"))
            out.append(
                SourceRef(
                    chunk_id=ch.chunk_id,
                    pdf_title=title,
                    section=section,
                    page=ch.page,
                    score=float(score),
                )
            )
        return out

    def _format_source_lines(self, refs: list[SourceRef], limit: int = 6) -> list[str]:
        seen: set[str] = set()
        lines: list[str] = []
        for r in refs:
            line = f"{r.pdf_title} - {r.section} (p.{r.page})"
            if line in seen:
                continue
            seen.add(line)
            lines.append(line)
            if len(lines) >= limit:
                break
        return lines

    def _tokens(self, text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"[가-힣A-Za-z0-9]{2,}", text)]

    def _extract_legal_refs(self, query: str) -> list[str]:
        pattern = re.compile(r"제\s*\d+\s*(?:장|절|조)(?:\s*의\s*\d+)?(?:\s*제?\d+\s*(?:항|호))?")
        refs = [re.sub(r"\s+", "", m.group(0)) for m in pattern.finditer(query)]
        seen: set[str] = set()
        out: list[str] = []
        for r in refs:
            if r not in seen:
                seen.add(r)
                out.append(r)
        return out

    def _correct_token(self, token: str) -> str:
        if token in self._TYPO_MAP:
            return self._TYPO_MAP[token]
        close = difflib.get_close_matches(token, self._domain_terms, n=1, cutoff=0.82)
        if close:
            return close[0]
        return token

    def _expand_synonyms(self, token: str) -> list[str]:
        expanded = {token}
        for g in self._SYNONYM_GROUPS:
            if token in g:
                expanded |= g
                break
        return sorted(expanded)

    def _build_query_plan(self, query: str) -> QueryPlan:
        normalized = re.sub(r"\s+", " ", query).strip()
        raw_tokens = [t for t in self._tokens(normalized) if len(t) >= 2]
        corrected = [self._correct_token(t) for t in raw_tokens]
        legal_refs = self._extract_legal_refs(normalized)

        terms: list[str] = []
        seen: set[str] = set()
        for t in corrected:
            for ex in self._expand_synonyms(t):
                if ex not in seen:
                    seen.add(ex)
                    terms.append(ex)
        for r in legal_refs:
            if r not in seen:
                seen.add(r)
                terms.append(r)

        bm25_query = " ".join(terms) if terms else normalized
        embedding_query = " ".join([normalized, bm25_query]).strip()
        return QueryPlan(
            raw_query=query,
            normalized_query=normalized,
            embedding_query=embedding_query,
            bm25_query=bm25_query,
            keyword_terms=terms,
            legal_refs=legal_refs,
        )

    def _kw_score_terms(self, query_terms: list[str], target: str | list[str]) -> float:
        q = {t.lower() for t in query_terms if t}
        if not q:
            return 0.0
        if isinstance(target, list):
            t = set(tok for k in target for tok in self._tokens(k))
            t |= {k.lower() for k in target if k}
        else:
            t = set(self._tokens(target))
            t.add(target.lower())
        if not t:
            return 0.0
        return len(q & t) / max(1, len(q))

    def _kw_score(self, query: str, target: str | list[str]) -> float:
        q = set(self._tokens(query))
        if not q:
            return 0.0
        if isinstance(target, list):
            t = set(tok for k in target for tok in self._tokens(k))
        else:
            t = set(self._tokens(target))
        if not t:
            return 0.0
        return len(q & t) / max(1, len(q))

    def _row_to_cat(self, row: Any) -> CatRec:
        c = row["c"]
        emb_raw = json.loads(c.get("embedding_json", "[]") or "[]")
        return CatRec(
            node_id=c["node_id"],
            name=c.get("name", ""),
            level=int(c.get("level", 0)),
            keywords=json.loads(c.get("keywords_json", "[]") or "[]"),
            embedding=np.array(emb_raw, dtype=np.float32) if emb_raw else None,
        )

    def _row_to_chunk(self, row: Any) -> ChunkRec:
        ch = row["ch"]
        emb_raw = json.loads(ch.get("embedding_json", "[]") or "[]")
        return ChunkRec(
            chunk_id=ch["chunk_id"],
            text=ch.get("text", ""),
            page=int(ch.get("page", 0)),
            doc_key=ch.get("doc_key", ""),
            embedding=np.array(emb_raw, dtype=np.float32) if emb_raw else None,
        )

    def _get_top_categories(self) -> list[CatRec]:
        with self.driver.session() as s:
            recs = s.run("MATCH (c:Category {level: 0}) RETURN c")
            return [self._row_to_cat(r) for r in recs]

    def _get_subcategories(self, top_ids: list[str]) -> list[CatRec]:
        if not top_ids:
            return []
        with self.driver.session() as s:
            recs = s.run(
                """
                MATCH (p:Category)-[:HAS_SUBCATEGORY]->(c:Category)
                WHERE p.node_id IN $ids
                RETURN c
                """,
                ids=top_ids,
            )
            return [self._row_to_cat(r) for r in recs]

    def _get_chunks_by_subcats(self, sub_ids: list[str]) -> list[ChunkRec]:
        if not sub_ids:
            return []
        with self.driver.session() as s:
            recs = s.run(
                """
                MATCH (ch:Chunk)-[:BELONGS_TO]->(c:Category)
                WHERE c.node_id IN $ids
                RETURN ch
                """,
                ids=sub_ids,
            )
            return [self._row_to_chunk(r) for r in recs]

    def _get_all_chunks(self) -> list[ChunkRec]:
        with self.driver.session() as s:
            recs = s.run("MATCH (ch:Chunk) RETURN ch")
            return [self._row_to_chunk(r) for r in recs]

    def _get_lexical_chunks(self, query_terms: list[str], limit: int = LEXICAL_CAND_LIMIT) -> list[ChunkRec]:
        tokens = [t.lower() for t in query_terms if len(t) >= 2][:12]
        if not tokens:
            return []
        with self.driver.session() as s:
            recs = s.run(
                """
                MATCH (ch:Chunk)
                WHERE any(tok IN $tokens WHERE toLower(ch.text) CONTAINS tok)
                RETURN ch
                LIMIT $limit
                """,
                tokens=tokens,
                limit=limit,
            )
            return [self._row_to_chunk(r) for r in recs]

    def _merge_chunks(self, *groups: list[ChunkRec]) -> list[ChunkRec]:
        merged: list[ChunkRec] = []
        seen: set[str] = set()
        for g in groups:
            for ch in g:
                if ch.chunk_id not in seen:
                    merged.append(ch)
                    seen.add(ch.chunk_id)
        return merged

    def _select_top_by_hybrid(self, query_terms: list[str], query_emb: np.ndarray, cats: list[CatRec], top_n: int) -> list[tuple[CatRec, float]]:
        if not cats:
            return []

        vec_scores = np.zeros(len(cats), dtype=np.float32)
        valid_idx = [i for i, c in enumerate(cats) if c.embedding is not None]
        if valid_idx:
            emb_mat = np.array([cats[i].embedding for i in valid_idx], dtype=np.float32)
            sims = cosine_similarity([query_emb], emb_mat)[0]
            for i, s in zip(valid_idx, sims):
                vec_scores[i] = float(s)

        scored: list[tuple[CatRec, float]] = []
        for i, c in enumerate(cats):
            kw = self._kw_score_terms(query_terms, c.keywords + [c.name])
            score = VEC_WEIGHT * float(vec_scores[i]) + KW_WEIGHT * kw
            scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def _score_chunks(
        self,
        query_terms: list[str],
        query_emb: np.ndarray,
        chunks: list[ChunkRec],
        legal_refs: Optional[list[str]] = None,
    ) -> list[tuple[ChunkRec, float]]:
        if not chunks:
            return []

        vec_scores = np.zeros(len(chunks), dtype=np.float32)
        valid_idx = [i for i, ch in enumerate(chunks) if ch.embedding is not None]
        if valid_idx:
            emb_mat = np.array([chunks[i].embedding for i in valid_idx], dtype=np.float32)
            sims = cosine_similarity([query_emb], emb_mat)[0]
            for i, s in zip(valid_idx, sims):
                vec_scores[i] = float(s)

        scored: list[tuple[ChunkRec, float]] = []
        legal_refs = legal_refs or []
        legal_refs_norm = [re.sub(r"\s+", "", lr).lower() for lr in legal_refs]
        for i, ch in enumerate(chunks):
            kw = self._kw_score_terms(query_terms, ch.text)
            legal_boost = 0.0
            if legal_refs_norm:
                text_norm = re.sub(r"\s+", "", ch.text).lower()
                if any(lr in text_norm for lr in legal_refs_norm):
                    legal_boost = 0.08
            score = min(1.0, VEC_WEIGHT * float(vec_scores[i]) + KW_WEIGHT * kw + legal_boost)
            scored.append((ch, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _dedup_semantic(self, scored_chunks: list[tuple[ChunkRec, float]], threshold: float) -> list[tuple[ChunkRec, float]]:
        if not scored_chunks:
            return []

        # 배치 인코딩: embedding 없는 청크를 한 번에 처리
        no_emb_idx = [i for i, (ch, _) in enumerate(scored_chunks) if ch.embedding is None]
        if no_emb_idx:
            texts = [scored_chunks[i][0].text for i in no_emb_idx]
            raw = self.embedder.encode(texts, show_progress_bar=False)
            embs = [raw] if len(no_emb_idx) == 1 else raw
            for i, emb in zip(no_emb_idx, embs):
                scored_chunks[i][0].embedding = np.asarray(emb, dtype=np.float32)

        # 전체 유사도 행렬을 미리 계산
        emb_mat = np.array([ch.embedding for ch, _ in scored_chunks], dtype=np.float32)
        norms = np.linalg.norm(emb_mat, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        emb_mat = emb_mat / norms
        sim_mat = emb_mat @ emb_mat.T  # cosine similarity (정규화 후 내적)

        selected: list[tuple[ChunkRec, float]] = []
        selected_indices: list[int] = []

        for i, (ch, score) in enumerate(scored_chunks):
            if not selected_indices or float(np.max(sim_mat[i, selected_indices])) < threshold:
                selected.append((ch, score))
                selected_indices.append(i)

        return selected

    def _mmr_rerank(self, scored_chunks: list[tuple[ChunkRec, float]], top_n: int, lambda_mult: float) -> list[tuple[ChunkRec, float]]:
        if not scored_chunks:
            return []
        if len(scored_chunks) <= top_n:
            return scored_chunks

        chunks = [c for c, _ in scored_chunks]
        relevance = np.array([float(s) for _, s in scored_chunks], dtype=np.float32)

        # 배치 인코딩: embedding 없는 청크를 한 번에 처리
        no_emb_idx = [i for i, ch in enumerate(chunks) if ch.embedding is None]
        if no_emb_idx:
            texts = [chunks[i].text for i in no_emb_idx]
            raw = self.embedder.encode(texts, show_progress_bar=False)
            embs = [raw] if len(no_emb_idx) == 1 else raw
            for i, emb in zip(no_emb_idx, embs):
                chunks[i].embedding = np.asarray(emb, dtype=np.float32)

        emb_mat = np.array([ch.embedding for ch in chunks], dtype=np.float32)
        norms = np.linalg.norm(emb_mat, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        emb_mat = emb_mat / norms
        sim_mat = emb_mat @ emb_mat.T  # cosine similarity (정규화 후 내적)

        selected_idx: list[int] = [int(np.argmax(relevance))]
        candidates = list(set(range(len(chunks))) - {selected_idx[0]})

        while candidates and len(selected_idx) < top_n:
            cand_arr = np.array(candidates)
            sel_arr = np.array(selected_idx)
            # 벡터화: 각 후보의 선택된 항목들과의 최대 유사도
            max_sims = np.max(sim_mat[np.ix_(cand_arr, sel_arr)], axis=1)
            mmr_scores = lambda_mult * relevance[cand_arr] - (1.0 - lambda_mult) * max_sims
            best_local = int(np.argmax(mmr_scores))
            best_idx = candidates[best_local]
            selected_idx.append(best_idx)
            candidates.pop(best_local)

        return [(chunks[i], float(relevance[i])) for i in selected_idx]

    def _llm_rerank(self, query: str, candidates: list[tuple[ChunkRec, float]], top_n: int) -> list[tuple[ChunkRec, float]]:
        if not ENABLE_LLM_RERANK or self.llm is None or not candidates:
            return candidates[:top_n]

        cand = candidates[: max(top_n, LLM_RERANK_CAND)]
        lines = []
        for ch, s in cand:
            preview = re.sub(r"\s+", " ", ch.text).strip()[:120]
            lines.append(f"- id={ch.chunk_id} score={s:.4f} text={preview}")

        prompt = (
            "질문과 관련성이 높은 청크 id를 고르세요. 다양성을 고려해 상위 id만 반환하세요.\n"
            "반환 형식: id를 콤마로만 나열 (설명 금지)\n"
            f"질문: {query}\n"
            "후보:\n"
            + "\n".join(lines)
        )

        try:
            resp = self.llm.generate_content(prompt, generation_config={"temperature": 0.0})
            text = (resp.text or "").strip()
            picked_ids = [x.strip() for x in re.split(r"[,\n]", text) if x.strip()]
            by_id = {ch.chunk_id: (ch, float(s)) for ch, s in cand}
            reranked: list[tuple[ChunkRec, float]] = []
            for cid in picked_ids:
                if cid in by_id:
                    reranked.append(by_id[cid])
            if reranked:
                existing = {ch.chunk_id for ch, _ in reranked}
                for ch, s in cand:
                    if ch.chunk_id not in existing:
                        reranked.append((ch, float(s)))
                    if len(reranked) >= top_n:
                        break
                return reranked[:top_n]
        except Exception:
            pass
        return cand[:top_n]

    def _needs_crawl(self, scored_chunks: list[tuple[ChunkRec, float]]) -> bool:
        if not scored_chunks:
            return True
        best = scored_chunks[0][1] if scored_chunks else 0.0
        # 둘 다 부족할 때만 정보 부족으로 간주하여 과도한 답변 거부를 줄입니다.
        return (len(scored_chunks) < MIN_CHUNKS_FOR_ANSWER) and (best < self.min_best_score)

    def _crawl_search(self, query: str) -> list[str]:
        q = urllib.parse.quote(query)
        url = f"https://duckduckgo.com/html/?q={q}"
        try:
            r = self.http.get(url, timeout=CRAWL_SEARCH_TIMEOUT)
            r.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        urls: list[str] = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if href.startswith("http"):
                urls.append(href)
            if len(urls) >= CRAWL_MAX_DOCS:
                break
        return urls

    def _fetch_page_text(self, url: str) -> str:
        try:
            r = self.http.get(url, timeout=CRAWL_FETCH_TIMEOUT)
            r.raise_for_status()
        except Exception:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        txt = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        return txt[:6000]

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        if not text:
            return []
        sents = re.split(r"(?<=[.!?。])\s+", text)
        out: list[str] = []
        buf = ""
        for s in sents:
            if len(buf) + len(s) > chunk_size and buf:
                out.append(buf.strip())
                buf = buf[-overlap:] + " " + s
            else:
                buf += (" " if buf else "") + s
        if buf.strip():
            out.append(buf.strip())
        return out

    def _crawl_fallback_chunks(self, query: str) -> list[tuple[str, str]]:
        urls = self._crawl_search(query)
        chunks: list[tuple[str, str]] = []
        for u in urls:
            txt = self._fetch_page_text(u)
            for c in self._chunk_text(txt):
                chunks.append((u, c))
            time.sleep(CRAWL_SLEEP_SEC)
        return chunks

    def _save_external_chunks(self, url_chunks: list[tuple[str, str]]) -> None:
        if not url_chunks:
            return
        emb = self.embedder.encode([c for _, c in url_chunks], show_progress_bar=False)
        with self.driver.session() as s:
            for (u, text), e in zip(url_chunks, emb):
                cid = hashlib.sha1((u + "|" + text[:120]).encode("utf-8")).hexdigest()[:20]
                s.run(
                    """
                    MERGE (src:ExternalSource {url: $url})
                    MERGE (ch:ExternalChunk {chunk_id: $cid})
                    SET ch.text = $text,
                        ch.embedding_json = $emb,
                        ch.fetched_at = datetime()
                    MERGE (src)-[:HAS_CHUNK]->(ch)
                    """,
                    url=u,
                    cid=cid,
                    text=text,
                    emb=json.dumps(np.asarray(e, dtype=np.float32).tolist()),
                )

    def _score_external_chunks(self, query: str, query_emb: np.ndarray, url_chunks: list[tuple[str, str]]) -> list[tuple[str, str, float]]:
        if not url_chunks:
            return []
        embs = self.embedder.encode([c for _, c in url_chunks], show_progress_bar=False)
        out: list[tuple[str, str, float]] = []
        for (u, c), e in zip(url_chunks, embs):
            vec = float(cosine_similarity([query_emb], [e])[0][0])
            kw = self._kw_score(query, c)
            score = VEC_WEIGHT * vec + KW_WEIGHT * kw
            out.append((u, c, score))
        out.sort(key=lambda x: x[2], reverse=True)
        return out

    def _local_action_guide(self, query: str, source_lines: list[str], reason: str, language: str) -> str:
        if language == "zh":
            lines = [
                "当前无法调用LLM，以下是本地引导模式。",
                f"- 原因: {reason}",
                f"- 问题: {query}",
                "",
                "建议行动:",
                "1. 先核对与问题直接相关的适用对象、时限、提交材料。",
                "2. 如果条款冲突，优先采用更新版本和官方来源。",
                "3. 提交前请再次确认主管机关或学校官网公告。",
                "",
                "证据来源:",
                *[f"- {p}" for p in source_lines[:6]],
            ]
            return "\n".join(lines)
        if language == "en":
            lines = [
                "LLM is unavailable, so this is a local guidance fallback.",
                f"- Reason: {reason}",
                f"- Question: {query}",
                "",
                "Recommended actions:",
                "1. Verify eligibility, deadlines, and required materials from the listed sources.",
                "2. If conditions conflict, prioritize newer and official statements.",
                "3. Before submission, confirm with the competent authority or university office.",
                "",
                "Evidence sources:",
                *[f"- {p}" for p in source_lines[:6]],
            ]
            return "\n".join(lines)

        lines = [
            "LLM 응답이 불가하여 로컬 가이드 모드로 안내합니다.",
            f"- 사유: {reason}",
            f"- 질문: {query}",
            "",
            "권장 행동 가이드:",
            "1. 아래 출처 목록에서 질문과 직접 관련된 요건(대상/기한/제출물)을 먼저 확인하세요.",
            "2. 같은 조건이 여러 문장에 있으면, 더 최신 조문/공식 출처를 우선 적용하세요.",
            "3. 실제 신청 전에 관할 기관 또는 학교 공식 안내를 최종 확인하세요.",
            "",
            "근거 출처:",
            *[f"- {p}" for p in source_lines[:6]],
        ]
        return "\n".join(lines)

    def _generate_answer(self, query: str, contexts: list[str], source_lines: list[str], language: str) -> str:
        if not contexts:
            return insufficient_evidence_message(language)
        if self.llm is None:
            return self._local_action_guide(query, source_lines, "LLM unavailable", language)

        prompt = build_answer_prompt(
            language=language,
            question_type=detect_question_type(query),
            query=query,
            context_block=self._format_context(contexts),
            evidence_lines=source_lines,
        )

        def _run_generate() -> str:
            resp = self.llm.generate_content(
                prompt,
                generation_config={"temperature": 0.0},
            )
            return (resp.text or "").strip() or "답변을 생성하지 못했습니다."

        try:
            return _run_generate()
        except gapi_exceptions.NotFound:
            # 모델 폐기/미지원 시 1회 자동 전환 후 재시도
            rebuilt = self._build_model()
            if rebuilt is not None:
                self.llm = rebuilt
                try:
                    return _run_generate()
                except Exception as e:
                    return self._local_action_guide(query, source_lines, f"LLM retry failed({self.model_name}): {e}", language)
            return self._local_action_guide(query, source_lines, "No Gemini model available", language)
        except gapi_exceptions.ResourceExhausted:
            return self._local_action_guide(query, source_lines, "Gemini quota exceeded", language)
        except Exception as e:
            return self._local_action_guide(query, source_lines, f"LLM error: {e}", language)

    def _retrieve_once(self, query: str) -> dict[str, Any]:
        query_plan = self._build_query_plan(query)
        query_emb = self.embedder.encode(query_plan.embedding_query)

        tops = self._select_top_by_hybrid(query_plan.keyword_terms, query_emb, self._get_top_categories(), TOP_CAT)
        top_ids = [c.node_id for c, _ in tops]
        subs = self._select_top_by_hybrid(query_plan.keyword_terms, query_emb, self._get_subcategories(top_ids), TOP_SUB)
        sub_ids = [c.node_id for c, _ in subs]

        routed_chunks = self._get_chunks_by_subcats(sub_ids)
        lexical_chunks = self._get_lexical_chunks(query_plan.keyword_terms)
        candidates = self._merge_chunks(routed_chunks, lexical_chunks)

        top_best = tops[0][1] if tops else 0.0
        sub_best = subs[0][1] if subs else 0.0
        if not candidates or (top_best <= 1e-9 and sub_best <= 1e-9):
            candidates = self._get_all_chunks()

        chunk_scored = self._score_chunks(
            query_plan.keyword_terms,
            query_emb,
            candidates,
            legal_refs=query_plan.legal_refs,
        )
        chunk_scored = chunk_scored[: TOP_CHUNK * 3]
        deduped = self._dedup_semantic(chunk_scored, threshold=SEM_DEDUP_THRESHOLD)
        mmr_ranked = self._mmr_rerank(deduped, top_n=TOP_CHUNK, lambda_mult=MMR_LAMBDA)
        final_internal = self._llm_rerank(query_plan.normalized_query, mmr_ranked, TOP_CHUNK)

        source_refs = self._build_source_refs(final_internal, FINAL_TOP)
        source_lines = self._format_source_lines(source_refs, limit=FINAL_TOP)

        return {
            "query_plan": query_plan,
            "tops": tops,
            "subs": subs,
            "final_internal": final_internal,
            "source_lines": source_lines,
        }

    def _retrieve_adapter(self, query: str, top_k: int) -> tuple[list[tuple[ChunkRec, float]], list[str]]:
        r = self._retrieve_once(query)
        return r["final_internal"][:top_k], r["source_lines"]

    def ask(self, query: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        language = detect_language(query)
        query = normalize_query(query)

        fast_result = self._retrieve_once(query)
        fast_chunks = fast_result["final_internal"]
        best_score = float(fast_chunks[0][1]) if fast_chunks else 0.0
        evidence_count = len(fast_chunks)

        use_deep, reasons = (
            best_score < self._gate.min_top_score
            or evidence_count < self._gate.min_evidence_chunks
            or detect_question_type(query).value in {"comparison", "cause", "exception"},
            [],
        )
        # run_deep_path 내부에서 동일 기준을 다시 점검하고 사유를 생성한다.

        selected_chunks = fast_chunks
        source_lines = fast_result["source_lines"]
        external_contexts: list[str] = []
        path = "fast"
        if use_deep:
            deep = run_deep_path(
                query_variants=expand_query(query, language),
                retrieve_fn=self._retrieve_adapter,
                top_k=TOP_CHUNK,
                thresholds=self._gate,
                web_client=self._web_client,
                enable_external=ENABLE_EXTERNAL_SEARCH,
            )
            selected_chunks = deep["chunks"]
            source_lines = deep["source_labels"]
            external_contexts = deep["external_contexts"]
            reasons = deep["reasons"]
            path = "deep"

        if not selected_chunks and not external_contexts:
            elapsed = round(time.perf_counter() - t0, 3)
            self._log_latency(path, elapsed, 0.0, 0)
            return {
                "query": query,
                "answered": False,
                "reason": "insufficient_context",
                "top_categories": [(c.name, float(s)) for c, s in fast_result["tops"]],
                "top_subcategories": [(c.name, float(s)) for c, s in fast_result["subs"]],
                "best_score": 0.0,
                "context_count": 0,
                "elapsed_sec": elapsed,
                "path": path,
                "gate_reasons": reasons,
                "answer": insufficient_evidence_message(language),
                "used_chunk_ids": [],
                "sources": [],
                "contexts": [],
            }

        used_chunk_ids = [ch.chunk_id for ch, _ in selected_chunks[:FINAL_TOP]]
        contexts: list[str] = [f"[DB][p.{ch.page}] {ch.text}" for ch, _ in selected_chunks[:FINAL_TOP]]
        contexts.extend(external_contexts)
        preview = source_lines[:3]

        answer = self._generate_answer(query, contexts, source_lines, language)
        elapsed = round(time.perf_counter() - t0, 3)
        top_score = float(selected_chunks[0][1]) if selected_chunks else 0.0
        self._log_latency(path, elapsed, top_score, len(selected_chunks))

        return {
            "query": query,
            "answered": True,
            "reason": "ok",
            "top_categories": [(c.name, float(s)) for c, s in fast_result["tops"]],
            "top_subcategories": [(c.name, float(s)) for c, s in fast_result["subs"]],
            "best_score": top_score,
            "context_count": len(contexts),
            "retrieved_preview": preview,
            "sources": source_lines,
            "used_chunk_ids": used_chunk_ids,
            "path": path,
            "gate_reasons": reasons,
            "query_forms": {
                "embedding_query": fast_result["query_plan"].embedding_query,
                "bm25_query": fast_result["query_plan"].bm25_query,
                "legal_refs": fast_result["query_plan"].legal_refs,
            },
            "elapsed_sec": elapsed,
            "answer": answer,
            "contexts": contexts,
        }

    def _log_latency(self, path: str, elapsed: float, best_score: float, evidence_count: int) -> None:
        append_latency_log(
            log_path=LATENCY_LOG_PATH,
            agent="hybrid_query_agent",
            path=path,
            elapsed=elapsed,
            best_score=best_score,
            evidence_count=evidence_count,
        )


def main() -> None:
    agent = HybridQueryAgent()
    print("Hybrid Query Agent ready. Enter question (or 'exit').")
    print("[INFO] DB 검색 전용 모드: DB 근거가 부족하면 답변하지 않습니다.")
    try:
        while True:
            try:
                q = input("\n질문> ").strip()
            except EOFError:
                print("\n[INFO] 입력 스트림 종료(EOF). 프로그램을 종료합니다.")
                break
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break
            print("[INFO] 질문 접수. 검색/생성 중...", flush=True)
            try:
                result = agent.ask(q)
                print("\n[상위 카테고리]", result["top_categories"])
                print("[하위 카테고리]", result["top_subcategories"])
                print("[답변 가능]", result["answered"])
                print("[최고 점수]", result.get("best_score", 0.0))
                print("[사용 청크 ID]", result.get("used_chunk_ids", []))
                print("\n[근거 출처]")
                for i, p in enumerate(result.get("retrieved_preview", []), start=1):
                    print(f"- 문서 {i}: {p}")
                print("[응답시간]", result["elapsed_sec"], "sec")
                print("\n[답변]\n" + result["answer"])
            except Exception as e:
                print(f"[ERROR] 질의 처리 실패: {e}")
    finally:
        agent.close()


if __name__ == "__main__":
    main()
