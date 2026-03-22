"""
유학생 생활 도우미 에이전트
────────────────────────────
외국인 유학생이 비자·학교생활·주거 등에 대해 질문하면
사용자 상태를 파악하고 맥락을 유지하며 답변합니다.

구조:
  1) 의도 분류        - 신청 / 기한 / 서류 / 상태갱신 / 일반
  2) 컨텍스트 구성    - 직전 3턴 + 사용자 프로필 주입
  3) RAG 검색         - 카테고리 라우팅 → 청크 수집 → 벡터 Top-K
  4) 답변 생성        - 의도별 프롬프트 + 근거 부족 차단
  5) 상태 업데이트    - 대화 히스토리 저장

의존 패키지:
    pip install neo4j google-generativeai numpy scikit-learn
    pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
    pip install sentence-transformers==3.0.1

.env 예시:
    GEMINI_API_KEY=AIzaSy...
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_password
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import google.generativeai as genai
import numpy as np
from google.api_core import exceptions as gapi_exceptions
from neo4j import GraphDatabase
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    _ST_ERROR: Optional[Exception] = None
except Exception as _e:
    SentenceTransformer = None  # type: ignore[assignment,misc]
    _ST_ERROR = _e


# ══════════════════════════════════════════════════════════════════
# 0. 환경 변수 로드
# ══════════════════════════════════════════════════════════════════

def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env()

GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.environ.get("GEMINI_MODEL", "gemini-3.0-flash")
NEO4J_URI       = os.environ.get("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER      = os.environ.get("NEO4J_USER",     os.environ.get("NEO4J_USERNAME", "neo4j"))
NEO4J_PASSWORD  = os.environ.get("NEO4J_PASSWORD", "")
EMBED_MODEL     = os.environ.get("EMBED_MODEL",    "jhgan/ko-sroberta-multitask")

TOP_CAT         = int(os.environ.get("TOP_CAT",   "3"))
TOP_SUB         = int(os.environ.get("TOP_SUB",   "5"))
TOP_K           = int(os.environ.get("TOP_K",     "6"))   # 최종 청크 수
HISTORY_TURNS   = int(os.environ.get("HISTORY_TURNS", "3"))  # 유지할 대화 턴 수
MIN_SCORE       = float(os.environ.get("MIN_SCORE", "0.25"))  # 근거 부족 판정 임계값


# ══════════════════════════════════════════════════════════════════
# 1. 데이터 구조
# ══════════════════════════════════════════════════════════════════

class Intent(Enum):
    """질문 의도 분류."""
    APPLICATION  = "application"   # 신청 방법
    DEADLINE     = "deadline"      # 기한·마감
    DOCUMENTS    = "documents"     # 필요 서류
    STATUS_UPDATE = "status_update" # 사용자 정보 갱신 ("나 D-2야", "다음달 체류기간 끝나")
    GENERAL      = "general"       # 일반 질문


@dataclass
class UserProfile:
    """
    사용자 상태. 대화 중 파악된 정보를 누적 저장.
    앱에서는 이 객체를 세션에 저장/로드해서 연속성 유지.
    """
    visa_type:       Optional[str] = None   # "D-2", "D-4" 등
    stay_until:      Optional[str] = None   # "2025-08-31" 형식
    school:          Optional[str] = None   # 대학교명
    entry_date:      Optional[str] = None   # "2024-03-01"
    nationality:     Optional[str] = None   # 국적
    extra: dict[str, str] = field(default_factory=dict)  # 기타 파악된 정보

    def to_context_str(self) -> str:
        """프롬프트에 주입할 사용자 상태 요약 문자열."""
        parts: list[str] = []
        if self.visa_type:
            parts.append(f"비자: {self.visa_type}")
        if self.stay_until:
            parts.append(f"체류기간 만료: {self.stay_until}")
        if self.school:
            parts.append(f"학교: {self.school}")
        if self.nationality:
            parts.append(f"국적: {self.nationality}")
        for k, v in self.extra.items():
            parts.append(f"{k}: {v}")
        return ", ".join(parts) if parts else "파악된 정보 없음"

    def is_empty(self) -> bool:
        return (
            self.visa_type is None
            and self.stay_until is None
            and self.school is None
            and self.nationality is None
            and not self.extra
        )


@dataclass
class Turn:
    """대화 한 턴."""
    role:    str   # "user" | "assistant"
    content: str


@dataclass
class CatRec:
    node_id:   str
    name:      str
    level:     int
    keywords:  list[str]
    embedding: Optional[np.ndarray]


@dataclass
class ChunkRec:
    chunk_id:  str
    text:      str
    page:      int
    doc_key:   str
    embedding: Optional[np.ndarray]


# ══════════════════════════════════════════════════════════════════
# 2. 폴백 임베더
# ══════════════════════════════════════════════════════════════════

class FallbackEmbedder:
    """torch 없이 동작하는 HashingVectorizer 기반 임베더."""

    def __init__(self, n_features: int = 768):
        self._vec = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            token_pattern=r"(?u)\b\w+\b",
        )

    def encode(self, texts: str | list[str], **_: Any) -> np.ndarray:
        single = isinstance(texts, str)
        lst    = [texts] if single else texts
        arr    = self._vec.transform(lst).toarray().astype(np.float32)
        return arr[0] if single else arr


# ══════════════════════════════════════════════════════════════════
# 3. 의도 분류기
# ══════════════════════════════════════════════════════════════════

class IntentClassifier:
    """
    규칙 기반 의도 분류.
    LLM 호출 없이 빠르게 분류해서 의도별 프롬프트를 선택.

    우선순위: STATUS_UPDATE > DOCUMENTS > APPLICATION > DEADLINE > GENERAL
    이유: "신청 서류 언제까지 제출해야 해?" 같은 복합 질문에서
         DEADLINE("언제")보다 DOCUMENTS/APPLICATION이 더 구체적인 의도이므로 먼저 검사.
    """

    # (의도, [(패턴, 가중치), ...]) — 먼저 선언된 의도가 우선순위 높음
    _PATTERNS: list[tuple[Intent, list[str]]] = [
        # 1순위: 사용자 정보 갱신 — 명확한 자기 소개 문장에만 매칭
        (Intent.STATUS_UPDATE, [
            r"나\s*[는은]\s*[A-Za-z]\d[-–]\d\s*비자",        # "나는 D-2 비자"
            r"내\s*비자\s*(?:종류|타입)?[는은이가]\s*[A-Za-z]",  # "내 비자는 D"
            r"(?:나|저)[의의]\s*체류기간\s*[이가]\s*\d",         # "나의 체류기간이 ~일"
            r"\d{4}[-./]\d{1,2}[-./]\d{1,2}[^\?]*(?:만료|종료|끝)",  # 날짜 + 만료 언급
            r"[A-Za-z]\d\s*[-–]\s*\d\s*(?:비자|visa)?\s*(?:야|이야)",   # "D-2야", "D-2 비자야"
            r"학교\s*[는은이가]\s*\S+(?:대학|university)",          # "학교는 한국대학교"
            r"국적\s*[은는이가]\s*\S+",                            # "국적은 중국"
        ]),
        # 2순위: 서류 — "뭐 필요" 계열
        (Intent.DOCUMENTS, [
            r"서류",
            r"서식",
            r"(?:뭐|무엇|어떤\s*것)[이가]?\s*필요",
            r"준비\s*(?:해야|할)\s*(?:할|하는)?\s*것",
            r"첨부\s*서류",
            r"제출\s*서류",
            r"신분증|여권|등록증",
        ]),
        # 3순위: 신청·절차 — "어떻게 해" 계열 (언제/기한 미포함)
        (Intent.APPLICATION, [
            r"(?:어떻게|어디서|어디에)\s*(?:신청|신고|등록|접수|발급)",
            r"신청\s*(?:방법|절차|하는\s*법)",
            r"(?:신청|신고|등록|접수|발급)\s*(?:방법|절차)",
            r"(?:방법|절차|과정)\s*(?:알려|궁금|모르)",
        ]),
        # 4순위: 기한 — 구체적인 기간·날짜 표현 (단순 "언제" 단어 단독 제외)
        (Intent.DEADLINE, [
            r"기한",
            r"마감",
            r"언제까지",
            r"며칠\s*(?:이내|안에|전에)",
            r"몇\s*일\s*(?:이내|안에|전에|남았)",
            r"(?:체류기간|비자)\s*(?:만료|연장|갱신)",
            r"(?:만료|연장|갱신)\s*(?:날짜|일자|기간)",
        ]),
    ]

    def classify(self, query: str) -> Intent:
        for intent, patterns in self._PATTERNS:
            for p in patterns:
                if re.search(p, query):
                    return intent
        return Intent.GENERAL


# ══════════════════════════════════════════════════════════════════
# 4. 사용자 상태 파서
# ══════════════════════════════════════════════════════════════════

class ProfileParser:
    """
    대화 텍스트에서 사용자 정보를 추출해 UserProfile을 갱신.
    STATUS_UPDATE 의도일 때 호출됨.
    """

    _VISA_RE   = re.compile(r"\b([A-Za-z][0-9][-–][0-9A-Za-z]?)\b")
    _DATE_RE   = re.compile(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})")
    _SCHOOL_RE = re.compile(r"([\w\s]+(?:대학교|대학|university|college))", re.IGNORECASE)

    def update(self, text: str, profile: UserProfile) -> UserProfile:
        """텍스트에서 파악된 정보를 profile에 덮어씀."""
        visa = self._VISA_RE.search(text)
        if visa:
            profile.visa_type = visa.group(1).upper()

        dates = self._DATE_RE.findall(text)
        if dates:
            # 마지막으로 언급된 날짜를 체류기간으로 간주
            profile.stay_until = dates[-1].replace("/", "-").replace(".", "-")

        school = self._SCHOOL_RE.search(text)
        if school:
            profile.school = school.group(1).strip()

        return profile


# ══════════════════════════════════════════════════════════════════
# 5. RAG 검색기 (단순화)
# ══════════════════════════════════════════════════════════════════

class SimpleRetriever:
    """
    카테고리 라우팅 → 청크 수집 → 벡터 유사도 Top-K.
    BM25 분리 / MMR / LLM 재랭킹 없음.
    """

    def __init__(self, driver: Any, embedder: Any):
        self._driver  = driver
        self._embedder = embedder

    def _encode(self, text: str) -> np.ndarray:
        return np.asarray(self._embedder.encode(text), dtype=np.float32)

    def _kw_score(self, query_tokens: set[str], target: str) -> float:
        if not query_tokens:
            return 0.0
        t_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", target.lower()))
        return len(query_tokens & t_tokens) / max(1, len(query_tokens))

    # ── Neo4j 쿼리 ──────────────────────────────────────────────

    def _get_top_cats(self) -> list[CatRec]:
        with self._driver.session() as s:
            rows = s.run("MATCH (c:Category {level:0}) RETURN c")
            return [self._row_to_cat(r) for r in rows]

    def _get_sub_cats(self, top_ids: list[str]) -> list[CatRec]:
        if not top_ids:
            return []
        with self._driver.session() as s:
            rows = s.run(
                "MATCH (p:Category)-[:HAS_SUBCATEGORY]->(c) WHERE p.node_id IN $ids RETURN c",
                ids=top_ids,
            )
            return [self._row_to_cat(r) for r in rows]

    def _get_chunks(self, sub_ids: list[str]) -> list[ChunkRec]:
        if not sub_ids:
            return []
        with self._driver.session() as s:
            rows = s.run(
                "MATCH (ch:Chunk)-[:BELONGS_TO]->(c) WHERE c.node_id IN $ids RETURN ch",
                ids=sub_ids,
            )
            return [self._row_to_chunk(r) for r in rows]

    def _get_all_chunks(self) -> list[ChunkRec]:
        with self._driver.session() as s:
            rows = s.run("MATCH (ch:Chunk) RETURN ch")
            return [self._row_to_chunk(r) for r in rows]

    def _fetch_source_labels(
        self, chunks: list[tuple[ChunkRec, float]]
    ) -> list[str]:
        """
        청크별로 문서명 + 카테고리명(섹션) + 페이지를 Neo4j에서 조회해
        "문서명 - 섹션 (p.12)" 형식의 출처 목록을 반환.
        조회 실패 시 "p.N" 형식으로 폴백.
        """
        if not chunks:
            return []

        chunk_ids = [ch.chunk_id for ch, _ in chunks]
        meta: dict[str, tuple[str, str]] = {}   # chunk_id → (doc_title, section)

        try:
            with self._driver.session() as s:
                rows = s.run(
                    """
                    UNWIND $ids AS cid
                    MATCH (ch:Chunk {chunk_id: cid})
                    OPTIONAL MATCH (d:Document {doc_key: ch.doc_key})
                    OPTIONAL MATCH (ch)-[:BELONGS_TO]->(cat:Category)
                    RETURN ch.chunk_id AS chunk_id,
                           coalesce(d.file_path, "") AS file_path,
                           coalesce(cat.name, "")    AS section,
                           coalesce(ch.doc_key, "")  AS doc_key
                    """,
                    ids=chunk_ids,
                )
                for r in rows:
                    fp    = r["file_path"] or ""
                    title = (
                        os.path.splitext(os.path.basename(fp))[0].strip()
                        if fp else f"문서-{(r['doc_key'] or '')[:6]}"
                    )
                    meta[r["chunk_id"]] = (title, r["section"] or "관련 내용")
        except Exception:
            pass  # DB 오류 시 폴백으로 처리

        labels: list[str] = []
        seen:   set[str]  = set()
        for ch, _ in chunks:
            title, section = meta.get(ch.chunk_id, ("", ""))
            if title:
                label = f"{title} - {section} (p.{ch.page})"
            else:
                label = f"p.{ch.page}"
            if label not in seen:
                seen.add(label)
                labels.append(label)
        return labels

    # ── 변환 유틸 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_cat(row: Any) -> CatRec:
        c = row["c"]
        emb = json.loads(c.get("embedding_json", "[]") or "[]")
        return CatRec(
            node_id   = c["node_id"],
            name      = c.get("name", ""),
            level     = int(c.get("level", 0)),
            keywords  = json.loads(c.get("keywords_json", "[]") or "[]"),
            embedding = np.array(emb, dtype=np.float32) if emb else None,
        )

    @staticmethod
    def _row_to_chunk(row: Any) -> ChunkRec:
        ch = row["ch"]
        emb = json.loads(ch.get("embedding_json", "[]") or "[]")
        return ChunkRec(
            chunk_id  = ch["chunk_id"],
            text      = ch.get("text", ""),
            page      = int(ch.get("page", 0)),
            doc_key   = ch.get("doc_key", ""),
            embedding = np.array(emb, dtype=np.float32) if emb else None,
        )

    # ── 하이브리드 점수 ─────────────────────────────────────────

    def _rank_cats(
        self,
        query_emb:    np.ndarray,
        query_tokens: set[str],
        cats:         list[CatRec],
        top_n:        int,
    ) -> list[CatRec]:
        if not cats:
            return []

        scored: list[tuple[CatRec, float]] = []
        valid_emb = [c for c in cats if c.embedding is not None]
        no_emb    = [c for c in cats if c.embedding is None]

        # 임베딩 있는 카테고리: 벡터 + 키워드 하이브리드
        if valid_emb:
            emb_mat = np.array([c.embedding for c in valid_emb])
            sims    = cosine_similarity([query_emb], emb_mat)[0]
            for c, sim in zip(valid_emb, sims):
                kw    = self._kw_score(query_tokens, c.name + " " + " ".join(c.keywords))
                score = 0.65 * float(sim) + 0.35 * kw
                scored.append((c, score))

        # 임베딩 없는 카테고리: 키워드 전용 폴백 (벡터 점수 0으로 처리)
        for c in no_emb:
            kw = self._kw_score(query_tokens, c.name + " " + " ".join(c.keywords))
            if kw > 0:  # 키워드가 조금이라도 겹치면 포함
                scored.append((c, 0.35 * kw))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_n]]

    def _rank_chunks(
        self,
        query_emb:    np.ndarray,
        query_tokens: set[str],
        chunks:       list[ChunkRec],
        top_k:        int,
    ) -> list[tuple[ChunkRec, float]]:
        if not chunks:
            return []

        valid_emb = [c for c in chunks if c.embedding is not None]
        no_emb    = [c for c in chunks if c.embedding is None]
        scored: list[tuple[ChunkRec, float]] = []

        # 임베딩 있는 청크: 벡터 + 키워드
        if valid_emb:
            emb_mat = np.array([c.embedding for c in valid_emb])
            sims    = cosine_similarity([query_emb], emb_mat)[0]
            for c, sim in zip(valid_emb, sims):
                kw    = self._kw_score(query_tokens, c.text)
                score = 0.65 * float(sim) + 0.35 * kw
                scored.append((c, score))

        # 임베딩 없는 청크: 키워드 전용 폴백
        for c in no_emb:
            kw = self._kw_score(query_tokens, c.text)
            if kw > 0:
                scored.append((c, 0.35 * kw))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ── 공개 인터페이스 ─────────────────────────────────────────

    def retrieve(
        self,
        query:   str,
        top_k:   int = TOP_K,
    ) -> tuple[list[tuple[ChunkRec, float]], list[str]]:
        """
        query → (청크+점수 목록, 출처 레이블 목록) 반환.
        카테고리 라우팅 실패 시 전체 청크에서 직접 검색.
        출처 형식: "문서명 - 섹션 (p.N)"
        """
        query_emb    = self._encode(query)
        query_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", query.lower()))

        # 상위 카테고리 Top 3
        top_cats = self._rank_cats(query_emb, query_tokens, self._get_top_cats(), TOP_CAT)
        # 하위 카테고리 Top K
        sub_cats = self._rank_cats(
            query_emb, query_tokens,
            self._get_sub_cats([c.node_id for c in top_cats]),
            TOP_SUB,
        )
        # 청크 후보 수집
        chunks = self._get_chunks([c.node_id for c in sub_cats])

        # 라우팅 결과 없으면 전체 청크 폴백
        if not chunks:
            chunks = self._get_all_chunks()

        # 하이브리드 점수로 Top-N 선정
        ranked = self._rank_chunks(query_emb, query_tokens, chunks, top_k)

        # 문서명 + 섹션 + 페이지 출처 레이블 조회
        source_labels = self._fetch_source_labels(ranked)

        return ranked, source_labels


# ══════════════════════════════════════════════════════════════════
# 6. 프롬프트 빌더 (의도별)
# ══════════════════════════════════════════════════════════════════

class PromptBuilder:
    """
    의도에 따라 LLM에게 전달할 프롬프트를 구성.
    모든 경우에 사용자 프로필 + 대화 히스토리를 포함.
    """

    _SYSTEM_BASE = (
        "당신은 한국에 사는 외국인 유학생을 돕는 친절한 생활 도우미입니다.\n"
        "반드시 아래 [근거 문서]에 있는 내용만 근거로 답변하세요.\n"
        "근거가 없으면 '제가 가진 자료에서 해당 내용을 찾지 못했어요.'라고 답하세요.\n"
        "답변은 한국어로, 유학생이 이해하기 쉽게 짧고 명확하게 작성하세요."
    )

    _FORMAT_MAP: dict[Intent, str] = {
        Intent.DEADLINE: (
            "형식:\n"
            "- 기한: (날짜 또는 기간)\n"
            "- 주의사항: (놓치면 생기는 문제)\n"
            "- 확인 방법: (한 줄)"
        ),
        Intent.DOCUMENTS: (
            "형식:\n"
            "필요 서류 목록 (번호 목록으로)\n"
            "- 특이사항이 있으면 괄호 안에 추가"
        ),
        Intent.APPLICATION: (
            "형식:\n"
            "신청 절차 (번호 목록, 3~5단계)\n"
            "- 제출 기관과 방법 포함"
        ),
        Intent.GENERAL: (
            "형식:\n"
            "핵심 답변 2~3문장, 필요하면 추가 안내 1줄"
        ),
        Intent.STATUS_UPDATE: "",  # 상태 갱신은 별도 처리
    }

    def build(
        self,
        query:         str,
        intent:        Intent,
        profile:       UserProfile,
        history:       list[Turn],
        chunks:        list[tuple[ChunkRec, float]],
        source_labels: list[str],
    ) -> str:
        # 근거 문서 블록
        context_block = "\n\n".join(
            f"[{i+1}] (p.{ch.page})\n{ch.text}"
            for i, (ch, _) in enumerate(chunks)
        )

        # 출처 블록
        source_block = ""
        if source_labels:
            source_block = "\n[출처]\n" + "\n".join(f"- {s}" for s in source_labels)

        # 대화 히스토리 블록
        history_block = ""
        if history:
            history_lines = [
                f"{'사용자' if t.role == 'user' else '어시스턴트'}: {t.content}"
                for t in history[-HISTORY_TURNS * 2:]
            ]
            history_block = "\n[이전 대화]\n" + "\n".join(history_lines)

        # 사용자 상태 블록
        profile_block = ""
        if not profile.is_empty():
            profile_block = f"\n[사용자 정보]\n{profile.to_context_str()}"

        # 의도별 출력 형식
        format_hint = self._FORMAT_MAP.get(intent, "")
        if format_hint:
            format_hint = "\n" + format_hint

        return (
            f"{self._SYSTEM_BASE}"
            f"{profile_block}"
            f"{history_block}"
            f"{format_hint}\n\n"
            f"[근거 문서]\n{context_block}"
            f"{source_block}\n\n"
            f"[질문]\n{query}"
        )

    def build_status_confirm(self, profile: UserProfile) -> str:
        """STATUS_UPDATE 의도: 파악한 정보 확인 메시지를 직접 생성."""
        return (
            f"확인했어요! 현재 파악된 정보:\n"
            f"{profile.to_context_str()}\n\n"
            "이 정보를 바탕으로 질문해주시면 더 정확하게 도와드릴게요."
        )


# ══════════════════════════════════════════════════════════════════
# 7. 메인 에이전트
# ══════════════════════════════════════════════════════════════════

class StudentAgent:
    """
    유학생 생활 도우미 에이전트.

    사용 예시 (앱 연동):
        agent = StudentAgent()

        # 세션 시작 시 프로필 로드 (없으면 빈 프로필)
        profile = UserProfile(visa_type="D-2", school="한국대학교")
        history: list[Turn] = []

        result = agent.ask("비자 연장 기한이 언제야?", profile, history)

        # 앱에 답변 전달
        print(result["answer"])

        # 히스토리 업데이트 (앱 세션에 저장)
        history = result["history"]
        profile = result["profile"]
    """

    def __init__(self) -> None:
        if not NEO4J_PASSWORD:
            raise ValueError(".env에 NEO4J_PASSWORD가 없습니다.")

        # Neo4j 연결
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self._driver.verify_connectivity()
        print("✅ Neo4j 연결 성공")

        # Gemini 초기화
        self._llm: Optional[genai.GenerativeModel] = None
        if GEMINI_API_KEY:
            self._llm = self._init_gemini()

        # 임베더 초기화
        self._embedder = self._init_embedder()
        self._is_fallback = isinstance(self._embedder, FallbackEmbedder)

        # 컴포넌트
        self._retriever  = SimpleRetriever(self._driver, self._embedder)
        self._classifier = IntentClassifier()
        self._parser     = ProfileParser()
        self._prompter   = PromptBuilder()

        # 폴백 임베더 시 점수 임계값 완화
        self._min_score = 0.08 if self._is_fallback else MIN_SCORE

    def close(self) -> None:
        self._driver.close()

    # ── 초기화 유틸 ────────────────────────────────────────────

    def _init_gemini(self) -> Optional[genai.GenerativeModel]:
        # 최신 모델을 앞에 배치. 환경변수 GEMINI_MODEL이 있으면 최우선 시도.
        preferred = [
            GEMINI_MODEL,            # .env 설정값 (없으면 기본값)
            "gemini-3.0-flash",
            "gemini-3-flash",
            "gemini-flash-latest",
            "gemini-2.0-flash",      # 하위 폴백
            "gemini-2.0-flash-lite", # 하위 폴백
            "gemini-1.5-flash",      # 구버전 폴백
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro-latest",
        ]
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            available = {
                m.name.replace("models/", "")
                for m in genai.list_models()
                if "generateContent" in (getattr(m, "supported_generation_methods", []) or [])
            }
            for name in preferred:
                if name in available:
                    if name != GEMINI_MODEL:
                        print(f"[INFO] Gemini 모델 자동 전환: {GEMINI_MODEL} → {name}")
                    else:
                        print(f"[INFO] Gemini 모델: {name}")
                    return genai.GenerativeModel(name)
            if available:
                # preferred 목록에 없는 모델이라도 최신순으로 선택
                name = sorted(available, reverse=True)[0]
                print(f"[INFO] Gemini 모델 자동선택(폴백): {name}")
                return genai.GenerativeModel(name)
        except Exception as e:
            print(f"[WARN] Gemini 초기화 실패: {e}")
        return None

    def _init_embedder(self) -> Any:
        if SentenceTransformer is None:
            print(f"[WARN] sentence-transformers 없음, 폴백 임베더 사용: {_ST_ERROR}")
            return FallbackEmbedder()
        try:
            return SentenceTransformer(EMBED_MODEL)
        except Exception as e:
            print(f"[WARN] SentenceTransformer 실패, 폴백 임베더 사용: {e}")
            return FallbackEmbedder()

    # ── 핵심 메서드 ─────────────────────────────────────────────

    def ask(
        self,
        query:   str,
        profile: UserProfile,
        history: list[Turn],
    ) -> dict[str, Any]:
        """
        질문 처리 후 결과 딕셔너리 반환.

        반환 키:
            answer      : str        - 최종 답변
            intent      : str        - 분류된 의도
            answered    : bool       - 근거 있는 답변 여부
            best_score  : float      - 최고 청크 유사도 점수
            profile     : UserProfile - 업데이트된 사용자 프로필
            history     : list[Turn] - 업데이트된 대화 히스토리
            sources     : list[str]  - 사용된 청크 출처 (page 목록)
            elapsed_sec : float
        """
        t0     = time.perf_counter()
        intent = self._classifier.classify(query)

        # ── 상태 갱신 의도: DB 검색 없이 프로필만 업데이트 ──
        if intent == Intent.STATUS_UPDATE:
            profile = self._parser.update(query, profile)
            answer  = self._prompter.build_status_confirm(profile)
            history = self._append_history(history, query, answer)
            return {
                "answer":      answer,
                "intent":      intent.value,
                "answered":    True,
                "best_score":  1.0,
                "profile":     profile,
                "history":     history,
                "sources":     [],
                "elapsed_sec": round(time.perf_counter() - t0, 3),
            }

        # ── 일반 의도: RAG 검색 + 답변 생성 ──

        # 3단계: RAG 검색 (카테고리 라우팅 → 청크 수집 → 하이브리드 Top-K)
        enriched_query = self._enrich_query(query, profile)
        chunks, source_labels = self._retriever.retrieve(enriched_query, top_k=TOP_K)

        # 근거 부족 판정
        best_score = float(chunks[0][1]) if chunks else 0.0
        if best_score < self._min_score or len(chunks) < 2:
            answer = (
                "죄송해요, 해당 질문에 대한 정확한 정보를 제가 가진 자료에서 찾지 못했어요.\n"
                "출입국·외국인청(1345) 또는 학교 국제처에 직접 문의해 보시는 걸 추천해요."
            )
            history = self._append_history(history, query, answer)
            return {
                "answer":      answer,
                "intent":      intent.value,
                "answered":    False,
                "best_score":  best_score,
                "profile":     profile,
                "history":     history,
                "sources":     [],
                "elapsed_sec": round(time.perf_counter() - t0, 3),
            }

        # 4단계: 답변 생성
        prompt = self._prompter.build(query, intent, profile, history, chunks, source_labels)
        answer = self._generate(query, prompt)

        # 5단계: 상태 업데이트
        history = self._append_history(history, query, answer)

        return {
            "answer":      answer,
            "intent":      intent.value,
            "answered":    True,
            "best_score":  best_score,
            "profile":     profile,
            "history":     history,
            "sources":     source_labels,   # "문서명 - 섹션 (p.N)" 형식
            "elapsed_sec": round(time.perf_counter() - t0, 3),
        }

    # ── 유틸 ───────────────────────────────────────────────────

    def _enrich_query(self, query: str, profile: UserProfile) -> str:
        """프로필의 비자·학교 정보를 쿼리에 덧붙여 검색 정확도 향상."""
        extra_parts: list[str] = []
        if profile.visa_type:
            extra_parts.append(profile.visa_type)
        if profile.school:
            extra_parts.append(profile.school)
        if not extra_parts:
            return query
        return f"{query} {' '.join(extra_parts)}"

    def _append_history(
        self,
        history: list[Turn],
        query:   str,
        answer:  str,
    ) -> list[Turn]:
        """히스토리에 현재 턴 추가. 최대 HISTORY_TURNS * 2 개 유지."""
        updated = history + [Turn("user", query), Turn("assistant", answer)]
        max_len = HISTORY_TURNS * 2
        return updated[-max_len:] if len(updated) > max_len else updated

    def _generate(self, query: str, prompt: str) -> str:
        """Gemini로 답변 생성. LLM 없거나 오류 시 폴백 메시지 반환."""
        if self._llm is None:
            return (
                "LLM이 설정되지 않아 답변을 생성할 수 없어요.\n"
                ".env에 GEMINI_API_KEY를 추가해주세요."
            )
        try:
            resp = self._llm.generate_content(
                prompt,
                generation_config={"temperature": 0.1},
            )
            return (resp.text or "").strip() or "답변을 생성하지 못했어요."

        except gapi_exceptions.ResourceExhausted:
            return (
                "현재 AI 서비스가 일시적으로 과부하 상태예요.\n"
                "잠시 후 다시 시도해주세요."
            )
        except gapi_exceptions.NotFound:
            # 모델 변경 후 1회 재시도
            self._llm = self._init_gemini()
            if self._llm:
                try:
                    resp = self._llm.generate_content(
                        prompt,
                        generation_config={"temperature": 0.1},
                    )
                    return (resp.text or "").strip()
                except Exception:
                    pass
            return "AI 모델 연결에 문제가 생겼어요. 잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"오류가 발생했어요: {e}"


# ══════════════════════════════════════════════════════════════════
# 8. 앱 연동용 간단 래퍼 (API 엔드포인트 예시)
# ══════════════════════════════════════════════════════════════════

class SessionStore:
    """
    인메모리 세션 저장소.

    ── 현재: 단일 프로세스 테스트용 ──
    프로세스 재시작 시 세션이 초기화됩니다.

    ── Redis로 교체하는 방법 ──
    pip install redis
    아래 주석 처리된 RedisSessionStore를 대신 사용하세요.

    class RedisSessionStore:
        def __init__(self, host="localhost", port=6379, db=0, ttl=3600):
            import redis
            self._r   = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self._ttl = ttl

        def get(self, user_id):
            raw = self._r.get(f"session:{user_id}")
            if not raw:
                return UserProfile(), []
            data    = json.loads(raw)
            profile = UserProfile(**data.get("profile", {}))
            history = [Turn(**t) for t in data.get("history", [])]
            return profile, history

        def save(self, user_id, profile, history):
            data = {
                "profile": {k: v for k, v in vars(profile).items() if v is not None},
                "history": [vars(t) for t in history],
            }
            self._r.setex(f"session:{user_id}", self._ttl, json.dumps(data, ensure_ascii=False))

        def reset(self, user_id):
            self._r.delete(f"session:{user_id}")
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get(self, user_id: str) -> tuple[UserProfile, list[Turn]]:
        data = self._store.get(user_id, {})
        return data.get("profile", UserProfile()), data.get("history", [])

    def save(self, user_id: str, profile: UserProfile, history: list[Turn]) -> None:
        self._store[user_id] = {"profile": profile, "history": history}

    def reset(self, user_id: str) -> None:
        self._store.pop(user_id, None)


# ── 앱 연동 예시 (FastAPI 사용 시 이 형태로 래핑) ──────────────

def handle_message(
    agent:   StudentAgent,
    session: SessionStore,
    user_id: str,
    message: str,
) -> dict[str, Any]:
    """
    앱의 메시지 핸들러. user_id 단위로 세션 관리.

    FastAPI 예시:
        @app.post("/chat")
        async def chat(req: ChatRequest):
            return handle_message(agent, session, req.user_id, req.message)
    """
    profile, history = session.get(user_id)
    result           = agent.ask(message, profile, history)
    session.save(user_id, result["profile"], result["history"])
    return {
        "answer":  result["answer"],
        "intent":  result["intent"],
        "sources": result["sources"],
    }


# ══════════════════════════════════════════════════════════════════
# 9. CLI 실행 (테스트용)
# ══════════════════════════════════════════════════════════════════

def main() -> None:
    agent   = StudentAgent()
    session = SessionStore()
    user_id = "test_user"

    print("유학생 도우미 시작. 'exit' 입력 시 종료.")
    print("사용자 정보 입력 예: '나는 D-2 비자야', '내 학교는 한국대학교야'")
    print("-" * 50)

    try:
        while True:
            try:
                q = input("\n질문> ").strip()
            except EOFError:
                break
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break

            result = agent.ask(q, *session.get(user_id))
            session.save(user_id, result["profile"], result["history"])

            print(f"[의도] {result['intent']}  |  [점수] {result['best_score']:.3f}  |  [{result['elapsed_sec']}s]")
            if result["sources"]:
                print(f"[출처] {', '.join(result['sources'])}")
            print(f"\n{result['answer']}")
    finally:
        agent.close()


if __name__ == "__main__":
    main()
