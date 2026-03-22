"""PDF 텍스트 파싱/청킹 모듈.

역할:
- 페이지별 텍스트 추출
- 문장 기반 청킹 생성
- 이후 카테고리/임베딩 단계가 쓰기 쉬운 형태로 정규화
"""

from __future__ import annotations

import re

import pdfplumber

from .config import CHUNK_OVERLAP, CHUNK_SIZE
from .models import Chunk


class PDFParser:
    """PDF를 페이지 텍스트와 청크 리스트로 변환하는 유틸 클래스."""
    @staticmethod
    def extract_text(pdf_path: str) -> list[tuple[int, str]]:
        pages: list[tuple[int, str]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                raw = page.extract_text() or ""
                lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines()]
                lines = [ln for ln in lines if ln]
                text = "\n".join(lines)
                if text:
                    pages.append((i, text))
        return pages

    @staticmethod
    def chunk_pages(
        pages: list[tuple[int, str]],
        size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        idx = 0
        for page_no, text in pages:
            sents = re.split(r"(?<=[.!?。])\s+", text)
            buf = ""
            for sent in sents:
                if len(buf) + len(sent) > size and buf:
                    chunks.append(Chunk(f"c{idx:04d}", buf.strip(), page_no))
                    idx += 1
                    buf = buf[-overlap:] + " " + sent
                else:
                    buf += (" " if buf else "") + sent
            if buf.strip():
                chunks.append(Chunk(f"c{idx:04d}", buf.strip(), page_no))
                idx += 1
        return chunks
