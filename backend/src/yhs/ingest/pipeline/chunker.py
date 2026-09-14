"""
yhs/ingest/pipeline/chunker.py

역할:
- 정제된 텍스트를 의미 단위 Chunk로 분할한다.
- 분할 우선순위:
    1순위: 명시적 섹션 헤더 패턴 (유형N, N단계, Q&A, Part N)
    2순위: 연속 두 줄 공백 (문단 경계)
    3순위: 512 토큰 초과 시 문장 단위 분할
- 50 토큰 미만 청크는 앞 청크에 병합한다.
- 출력: (text, section) 튜플 목록
"""

from __future__ import annotations

import hashlib
import re

from yhs.core.config import MAX_CHUNK_TOKENS, MIN_CHUNK_TOKENS
from yhs.schema.types import ChunkNode, RawDocument

# 섹션 헤더 패턴 (분할 기준)
_SECTION_HEADER_RE = re.compile(
    r"(?m)^(?:유형\s*\d+|(?:\d+\s*단계)|(?:Part\s*\d+)|(?:Q\s*&\s*A)|(?:제\s*\d+\s*[조장절])|(?:■|●|◆|\d+\.))\s*.{0,40}$"
)
# 문장 분리 패턴 (한국어 + 영어)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。])\s+")


_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer

        from yhs.core.config import EMBEDDING_MODEL
        _tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
    return _tokenizer


def _token_count(text: str) -> int:
    return len(_get_tokenizer().encode(text, add_special_tokens=False))


def _split_by_sentences(text: str, max_tokens: int) -> list[str]:
    """문장 단위로 분할하여 max_tokens 이하 청크를 생성한다."""
    sentences = _SENTENCE_SPLIT_RE.split(text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        st = _token_count(sentence)
        if current_tokens + st > max_tokens and current:
            chunks.append(" ".join(current))
            current = [sentence]
            current_tokens = st
        else:
            current.append(sentence)
            current_tokens += st

    if current:
        chunks.append(" ".join(current))
    return chunks


def _split_raw_text(text: str) -> list[tuple[str, str]]:
    """
    텍스트를 청킹 우선순위에 따라 (chunk_text, section) 튜플 목록으로 반환한다.
    """
    # 1순위: 섹션 헤더로 분할
    parts = _SECTION_HEADER_RE.split(text)
    headers = _SECTION_HEADER_RE.findall(text)

    segments: list[tuple[str, str]] = []  # (text, section_header)
    if len(parts) > 1:
        for i, part in enumerate(parts):
            header = headers[i - 1].strip() if i > 0 and i - 1 < len(headers) else ""
            if part.strip():
                segments.append((part.strip(), header))
    else:
        segments = [(text, "")]

    # 2순위: 문단 경계로 추가 분할
    result: list[tuple[str, str]] = []
    for (seg_text, section) in segments:
        paragraphs = re.split(r"\n{2,}", seg_text)
        for para in paragraphs:
            para = para.strip()
            if para:
                result.append((para, section))

    return result


def chunk_document(doc: RawDocument) -> list[ChunkNode]:
    """
    RawDocument 하나를 ChunkNode 목록으로 변환한다.
    """
    segments = _split_raw_text(doc.text)
    chunks: list[ChunkNode] = []
    buffer_text = ""
    buffer_section = doc.section

    def flush(text: str, section: str) -> None:
        nonlocal chunks
        if _token_count(text) > MAX_CHUNK_TOKENS:
            for sub in _split_by_sentences(text, MAX_CHUNK_TOKENS):
                if sub.strip():
                    chunks.append(_make_chunk(sub.strip(), section, doc))
        else:
            if text.strip():
                chunks.append(_make_chunk(text.strip(), section, doc))

    for seg_text, section in segments:
        tc = _token_count(seg_text)
        if tc < MIN_CHUNK_TOKENS:
            # 50 토큰 미만 → 앞 버퍼에 병합
            buffer_text = (buffer_text + "\n" + seg_text).strip() if buffer_text else seg_text
        else:
            if buffer_text:
                flush(buffer_text, buffer_section)
                buffer_text = ""
            flush(seg_text, section or doc.section)
            buffer_section = section or doc.section

    if buffer_text:
        flush(buffer_text, buffer_section)

    return chunks


def _make_chunk(text: str, section: str, doc: RawDocument) -> ChunkNode:
    # id 는 내용에서 결정한다 (랜덤 UUID 금지).
    #
    # 적재는 graph_store 에서 `MERGE (n:Chunk {id: $id})` 로 이뤄지는데,
    # id 가 매 실행마다 달라지면 MERGE 가 의미를 잃고 인제스트를 돌릴 때마다
    # 같은 내용이 통째로 복제된다. 실제로 그렇게 쌓인 적이 있다 —
    # 342개 청크 중 고유 텍스트가 158개뿐이었고(2~4배 중복), 검색 top-6 이
    # 사실상 top-2 로 줄어 근거 다양성이 크게 손상됐다.
    #
    # 같은 파일·같은 페이지·같은 본문이면 언제 돌려도 같은 id 가 나오므로
    # 재인제스트가 멱등해진다.
    fingerprint = f"{doc.source_file}|{doc.source_page}|{text}"
    chunk_id = "chunk_" + hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return ChunkNode(
        id=chunk_id,
        text=text,
        source_file=doc.source_file,
        source_page=doc.source_page,
        section=section,
        language=doc.language,
        doc_version=doc.doc_version,
    )
