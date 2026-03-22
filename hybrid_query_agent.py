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

    def close(self) -> None:
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

        selected: list[tuple[ChunkRec, float]] = []
        selected_vecs: list[np.ndarray] = []

        for ch, score in scored_chunks:
            vec = ch.embedding
            if vec is None:
                vec = self.embedder.encode(ch.text)
                ch.embedding = vec

            is_dup = False
            if selected_vecs:
                sims = cosine_similarity([vec], selected_vecs)[0]
                if float(np.max(sims)) >= threshold:
                    is_dup = True

            if not is_dup:
                selected.append((ch, score))
                selected_vecs.append(vec)

        return selected

    def _mmr_rerank(self, scored_chunks: list[tuple[ChunkRec, float]], top_n: int, lambda_mult: float) -> list[tuple[ChunkRec, float]]:
        if not scored_chunks:
            return []
        if len(scored_chunks) <= top_n:
            return scored_chunks

        chunks = [c for c, _ in scored_chunks]
        relevance = np.array([float(s) for _, s in scored_chunks], dtype=np.float32)
        embeddings: list[np.ndarray] = []
        for ch in chunks:
            vec = ch.embedding
            if vec is None:
                vec = self.embedder.encode(ch.text)
                ch.embedding = vec
            embeddings.append(vec)
        emb_mat = np.array(embeddings, dtype=np.float32)
        sim_mat = cosine_similarity(emb_mat, emb_mat)

        selected_idx: list[int] = [int(np.argmax(relevance))]
        candidates = set(range(len(chunks))) - set(selected_idx)

        while candidates and len(selected_idx) < top_n:
            best_idx = -1
            best_mmr = -1e9
            for idx in candidates:
                max_sim = max(float(sim_mat[idx][j]) for j in selected_idx)
                mmr = lambda_mult * float(relevance[idx]) - (1.0 - lambda_mult) * max_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = idx
            if best_idx < 0:
                break
            selected_idx.append(best_idx)
            candidates.remove(best_idx)

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

    def _local_action_guide(self, query: str, source_lines: list[str], reason: str) -> str:
        lines = [
            "LLM 응답이 불가하여 로컬 가이드 모드로 안내합니다.",
            f"- 사유: {reason}",
            f"- 질문: {query}",
            "",
            "권장 행동 가이드:",
            "1. 아래 출처 목록에서 질문과 직접 관련된 요건(대상/기한/제출물)을 먼저 확인하세요.",
            "2. 같은 조건이 여러 문장에 있으면, 더 최신 조문/공식 출처를 우선 적용하세요.",
            "3. 실제 신청/신고 전에 관할 기관 공식 안내(출입국·민원 포털)를 최종 확인하세요.",
            "",
            "근거 출처:",
            *[f"- {p}" for p in source_lines[:6]],
        ]
        return "\n".join(lines)

    def _generate_answer(self, query: str, contexts: list[str], source_lines: list[str]) -> str:
        if not contexts:
            return "관련 정보를 찾지 못했습니다."
        if self.llm is None:
            return self._local_action_guide(query, source_lines, "LLM 미사용")

        # test.py의 템플릿형 구성을 반영해 프롬프트를 명확히 분리합니다.
        prompt_template = (
            "당신은 실무 가이드 전문가입니다. 아래 컨텍스트만 근거로 답변하세요.\n"
            "절대 컨텍스트에 없는 사실을 추정하지 마세요.\n"
            "출력은 반드시 한국어로, 아래 형식을 지키세요:\n"
            "1) 핵심 답변: 질문에 대한 결론 2~4문장\n"
            "2) 사용자가 지금 해야 할 행동: 번호 목록 3~6개\n"
            "3) 준비할 것/확인할 것: 체크리스트\n"
            "4) 근거 출처: 아래 [출처목록]에서만 선택해 '문서명 - 항목명 (p.페이지)' 형식으로 2~6개\n"
            "중요: 근거에 본문 문장을 인용/복붙하지 마세요. 출처 라인만 적으세요.\n"
            "근거가 약하면 그 사실과 추가 확인 방법을 명시하세요.\n\n"
            "[출처목록]\n{sources}\n\n"
            "[질문]\n{question}\n\n[컨텍스트]\n{context}"
        )
        prompt = prompt_template.format(
            question=query,
            context=self._format_context(contexts),
            sources="\n".join(f"- {s}" for s in source_lines),
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
                    return self._local_action_guide(query, source_lines, f"LLM 재시도 실패({self.model_name}): {e}")
            return self._local_action_guide(query, source_lines, "사용 가능한 Gemini 모델을 찾지 못함")
        except gapi_exceptions.ResourceExhausted:
            return self._local_action_guide(query, source_lines, "Gemini 쿼터 초과")
        except Exception as e:
            return self._local_action_guide(query, source_lines, f"LLM 오류: {e}")

    def ask(self, query: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        query_plan = self._build_query_plan(query)
        query_emb = self.embedder.encode(query_plan.embedding_query)

        # 1) 상위 카테고리 Top 3
        tops = self._select_top_by_hybrid(query_plan.keyword_terms, query_emb, self._get_top_categories(), TOP_CAT)
        top_ids = [c.node_id for c, _ in tops]

        # 2) 하위 카테고리 Top K
        subs = self._select_top_by_hybrid(query_plan.keyword_terms, query_emb, self._get_subcategories(top_ids), TOP_SUB)
        sub_ids = [c.node_id for c, _ in subs]

        # 3) 하위 소속 청크 수집 + 하이브리드 점수
        routed_chunks = self._get_chunks_by_subcats(sub_ids)
        lexical_chunks = self._get_lexical_chunks(query_plan.keyword_terms)

        # 계층 라우팅 + 키워드 후보를 합쳐 누락을 줄입니다.
        candidates = self._merge_chunks(routed_chunks, lexical_chunks)

        # 계층 라우팅 점수가 전부 0 근처면 전체 청크에서 직접 검색 (폴백 경로)
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

        # 8) 의미적 중복 제거
        deduped = self._dedup_semantic(chunk_scored, threshold=SEM_DEDUP_THRESHOLD)

        # 7) 재랭킹: MMR 기본 + 선택적 LLM 재랭킹
        mmr_ranked = self._mmr_rerank(deduped, top_n=TOP_CHUNK, lambda_mult=MMR_LAMBDA)
        final_internal = self._llm_rerank(query_plan.normalized_query, mmr_ranked, TOP_CHUNK)

        used_chunk_ids = [ch.chunk_id for ch, _ in final_internal[:FINAL_TOP]]

        # 4) DB 정보 부족이면 답변 생성을 중단
        if self._needs_crawl(final_internal):
            return {
                "query": query,
                "answered": False,
                "reason": "insufficient_db_context",
                "top_categories": [(c.name, float(s)) for c, s in tops],
                "top_subcategories": [(c.name, float(s)) for c, s in subs],
                "best_score": float(final_internal[0][1]) if final_internal else 0.0,
                "context_count": len(final_internal),
                "elapsed_sec": round(time.perf_counter() - t0, 3),
                "answer": "DB에 충분한 근거 정보가 없어 답변을 생성하지 않습니다.",
                "used_chunk_ids": [],
                "query_forms": {
                    "embedding_query": query_plan.embedding_query,
                    "bm25_query": query_plan.bm25_query,
                    "legal_refs": query_plan.legal_refs,
                },
                "contexts": [],
            }

        # 5) 재랭킹(간단): 내부/외부 후보를 합치고 점수순
        contexts: list[tuple[str, float]] = []
        for ch, s in final_internal:
            contexts.append((f"[DB][p.{ch.page}] {ch.text}", s))
        source_refs = self._build_source_refs(final_internal, FINAL_TOP)
        source_lines = self._format_source_lines(source_refs, limit=FINAL_TOP)
        final_contexts = [c for c, _ in contexts[:FINAL_TOP]]
        preview = source_lines[:3]

        answer = self._generate_answer(query, final_contexts, source_lines)

        return {
            "query": query,
            "answered": True,
            "reason": "ok",
            "top_categories": [(c.name, float(s)) for c, s in tops],
            "top_subcategories": [(c.name, float(s)) for c, s in subs],
            "best_score": float(final_contexts and contexts[0][1] or 0.0),
            "context_count": len(final_contexts),
            "retrieved_preview": preview,
            "sources": source_lines,
            "used_chunk_ids": used_chunk_ids,
            "query_forms": {
                "embedding_query": query_plan.embedding_query,
                "bm25_query": query_plan.bm25_query,
                "legal_refs": query_plan.legal_refs,
            },
            "elapsed_sec": round(time.perf_counter() - t0, 3),
            "answer": answer,
            "contexts": source_lines,
        }


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
