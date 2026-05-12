"""
graph_rag/pipeline/loader.py

역할:
- PDF 파일: pdfplumber로 페이지별 텍스트·섹션 헤더 추출
- 출력: RawDocument 목록 (text, source_file, source_page, section, ...)

※ 웹 크롤링(WebLoader)은 agent/crawler 로 이전되었습니다.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

from graph_rag.schema.types import RawDocument

logger = logging.getLogger(__name__)

# 섹션 헤더 패턴 (PDF)
_SECTION_PATTERNS = [
    re.compile(r"유형\s*\d+", re.IGNORECASE),
    re.compile(r"\d+\s*단계"),
    re.compile(r"Part\s*\d+", re.IGNORECASE),
    re.compile(r"Q\s*&\s*A", re.IGNORECASE),
    re.compile(r"제\s*\d+\s*[조장절]"),
]


def _detect_section(text: str) -> str:
    """텍스트 블록의 섹션 헤더를 감지해 반환한다."""
    for pattern in _SECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(0)
    return ""


def _detect_doc_version(filename: str) -> str:
    """파일명에서 연도.월 형식의 버전 정보를 추출한다."""
    m = re.search(r"(\d{4})[._-](\d{2})", filename)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return ""


class PDFLoader:
    """pdfplumber 기반 PDF 텍스트 수집기."""

    def load(self, pdf_path: Path) -> List[RawDocument]:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber를 설치하세요: pip install pdfplumber")

        docs: List[RawDocument] = []
        doc_version = _detect_doc_version(pdf_path.name)

        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_section = ""
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    if not text.strip():
                        continue

                    # 섹션 헤더 갱신
                    detected = _detect_section(text)
                    if detected:
                        current_section = detected

                    docs.append(RawDocument(
                        text=text,
                        source_file=pdf_path.name,
                        source_page=page_num,
                        section=current_section,
                        language="ko",
                        doc_version=doc_version,
                    ))
        except Exception as exc:
            logger.error("PDF 로딩 실패 (%s): %s", pdf_path, exc)

        logger.info("PDF 로드 완료: %s (%d 페이지)", pdf_path.name, len(docs))
        return docs


# WebLoader는 agent/crawler 로 이전되었습니다.
