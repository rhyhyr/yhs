"""
yhs/ingest/pipeline/chunker.py

역할:
- 정제된 텍스트를 의미 단위 Chunk로 분할한다.
- 분할 우선순위:
    1순위: 명시적 섹션 헤더 패턴 (유형N, N단계, Q&A, Part N)
    2순위: 연속 두 줄 공백 (문단 경계)
    3순위: MAX_CHUNK_TOKENS 초과 시 문장 단위 분할
- 세그먼트를 CHUNK_SIZE 목표치까지 모아 하나의 청크로 만들고,
  인접 청크 사이에 CHUNK_OVERLAP 만큼 겹침을 둔다.
- MIN_CHUNK_TOKENS 미만 자투리는 앞 청크에 병합한다.
- 청크 id 는 (파일·페이지·본문) 해시라 재인제스트가 멱등하다.
"""

from __future__ import annotations

import hashlib
import re

from yhs.core.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    MAX_CHUNK_TOKENS,
    MIN_CHUNK_TOKENS,
)
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


def _tail_by_tokens(text: str, n_tokens: int) -> str:
    """텍스트 끝에서 n_tokens 만큼을 문장 경계에 맞춰 잘라 낸다 (오버랩용)."""
    if n_tokens <= 0 or not text:
        return ""
    sentences = _SENTENCE_SPLIT_RE.split(text)
    tail: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        st = _token_count(sentence)
        if total + st > n_tokens and tail:
            break
        tail.insert(0, sentence)
        total += st
    return " ".join(tail).strip()


def chunk_document(doc: RawDocument) -> list[ChunkNode]:
    """RawDocument 하나를 ChunkNode 목록으로 변환한다.

    세그먼트(섹션 헤더 → 문단)를 CHUNK_SIZE 목표치까지 모아서 하나의 청크로
    내보내고, 인접 청크 사이에 CHUNK_OVERLAP 만큼 겹침을 둔다.

    예전에는 문단 하나를 그대로 청크로 만들고 50 토큰 미만만 앞에 붙였다.
    그 결과 median 157 토큰(bge-m3 한도 8192의 2%)까지 잘게 쪼개졌고,
    오버랩이 없어 한 절차의 '대상 및 시기'와 '제출 서류'가 서로 다른
    청크로 갈라져 한쪽만 검색되는 일이 잦았다.
    """
    segments = _split_raw_text(doc.text)
    chunks: list[ChunkNode] = []

    buffer: list[str] = []
    buffer_tokens = 0
    carried_tokens = 0          # 버퍼 중 앞 청크에서 넘어온 오버랩 분량
    buffer_section = doc.section

    def emit() -> None:
        """현재 버퍼를 청크로 내보내고, 꼬리를 다음 버퍼로 넘긴다."""
        nonlocal buffer, buffer_tokens, carried_tokens
        text = "\n".join(buffer).strip()
        if not text:
            buffer, buffer_tokens, carried_tokens = [], 0, 0
            return
        chunks.append(_make_chunk(text, buffer_section, doc))

        tail = _tail_by_tokens(text, CHUNK_OVERLAP)
        if tail:
            buffer = [tail]
            buffer_tokens = _token_count(tail)
            carried_tokens = buffer_tokens
        else:
            buffer, buffer_tokens, carried_tokens = [], 0, 0

    for seg_text, section in segments:
        if section:
            buffer_section = section
        seg_tokens = _token_count(seg_text)

        # 단독으로 상한을 넘는 세그먼트는 문장 단위로 쪼개 바로 내보낸다.
        if seg_tokens > MAX_CHUNK_TOKENS:
            if buffer_tokens > carried_tokens:
                emit()
            for sub in _split_by_sentences(seg_text, MAX_CHUNK_TOKENS):
                if sub.strip():
                    chunks.append(_make_chunk(sub.strip(), buffer_section, doc))
            buffer, buffer_tokens, carried_tokens = [], 0, 0
            continue

        # 목표치를 넘기면 지금까지 모은 것을 먼저 내보낸다.
        if buffer_tokens + seg_tokens > CHUNK_SIZE and buffer_tokens > carried_tokens:
            emit()

        buffer.append(seg_text)
        buffer_tokens += seg_tokens

    # 남은 버퍼: 오버랩만 남은 경우는 이미 앞 청크에 담겨 있으므로 버린다.
    if buffer_tokens > carried_tokens:
        text = "\n".join(buffer).strip()
        if text:
            # 자투리가 최소치에 못 미치면 독립 청크로 두지 않고 앞 청크에 붙인다.
            # 예전에는 그대로 내보내서 전체의 14%가 50 토큰 미만이었고,
            # 그중 12개는 30 토큰도 안 되는 사실상 정보가 없는 조각이었다.
            if chunks and _token_count(text) < MIN_CHUNK_TOKENS:
                prev = chunks[-1]
                merged = f"{prev.text}\n{text}".strip()
                chunks[-1] = _make_chunk(merged, prev.section, doc)
            else:
                chunks.append(_make_chunk(text, buffer_section, doc))

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
