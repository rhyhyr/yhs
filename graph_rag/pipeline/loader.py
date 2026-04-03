"""
graph_rag/pipeline/loader.py

역할:
- PDF 파일: pdfplumber로 페이지별 텍스트·섹션 헤더 추출
- 공지사항 웹 URL: requests + BeautifulSoup4 HTML 파싱
- 출력: RawDocument 목록 (text, source_file, source_page, section, ...)
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup

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


class WebLoader:
    """requests + BeautifulSoup 기반 웹 공지사항 수집기."""

    def __init__(self, timeout: int = 15) -> None:
        self._timeout = timeout

    def load(self, url: str) -> List[RawDocument]:
        try:
            resp = requests.get(url, timeout=self._timeout)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("웹 수집 실패 (%s): %s", url, exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 제목 추출
        title_tag = soup.find(["h1", "h2", "h3", "title"])
        title = title_tag.get_text(strip=True) if title_tag else ""

        # 날짜 추출 (공지사항 신선도 관리용)
        doc_version = ""
        date_patterns = [
            re.compile(r"\d{4}[-./]\d{2}[-./]\d{2}"),
            re.compile(r"\d{4}년\s*\d{1,2}월"),
        ]
        page_text = soup.get_text()
        for pat in date_patterns:
            m = pat.search(page_text)
            if m:
                raw = m.group(0).replace("년", ".").replace("월", "").replace(" ", "")
                doc_version = raw[:7]  # YYYY.MM
                break

        # 본문 블록 추출: <article>, <main>, <div.content> 순으로 시도
        content_tag = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"content|post|article", re.I))
            or soup.find("body")
        )
        if not content_tag:
            return []

        # 문단 단위로 분리
        paragraphs = [
            p.get_text(separator=" ", strip=True)
            for p in content_tag.find_all(["p", "li", "td", "div"])
            if len(p.get_text(strip=True)) > 20
        ]

        if not paragraphs:
            paragraphs = [page_text]

        full_text = "\n\n".join(paragraphs)
        filename = hashlib.md5(url.encode()).hexdigest()[:12] + ".html"

        docs = [RawDocument(
            text=full_text,
            source_file=filename,
            source_page=1,
            section=title,
            language="ko",
            doc_version=doc_version,
            source_url=url,
        )]

        logger.info("웹 로드 완료: %s (버전: %s)", url, doc_version)
        return docs

    def get_content_hash(self, url: str) -> str:
        """신선도 감지용 URL 콘텐츠 MD5 해시를 반환한다."""
        try:
            resp = requests.get(url, timeout=self._timeout)
            return hashlib.md5(resp.content).hexdigest()
        except Exception:
            return ""
