from __future__ import annotations

import logging
import os
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from .models import WebSnippet

logger = logging.getLogger(__name__)


class WebSearchClient:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.allowed_suffixes = self._load_allowed_suffixes()

    def close(self) -> None:
        self.session.close()

    def search_and_collect(self, query: str, max_results: int = 3) -> list[WebSnippet]:
        urls = self._search_urls(query, max_results=max_results * 3)
        snippets: list[WebSnippet] = []
        for u in urls:
            final_url = self._resolve_final_url(u)
            if not final_url:
                continue
            if not self._is_allowed_url(final_url):
                continue
            text = self._fetch_text(final_url)
            if not text:
                continue
            title = self._title_from_url(final_url)
            snippets.append(WebSnippet(url=final_url, title=title, snippet=text[:1200]))
            if len(snippets) >= max_results:
                break
        return snippets

    def _search_urls(self, query: str, max_results: int) -> list[str]:
        q = urllib.parse.quote(query)
        url = f"https://duckduckgo.com/html/?q={q}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        out: list[str] = []
        for a in soup.select("a.result__a"):
            href = (a.get("href") or "").strip()
            if href.startswith("http"):
                out.append(href)
            if len(out) >= max_results:
                break
        return out

    def _resolve_final_url(self, url: str) -> str:
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            return resp.url
        except Exception:
            return ""

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        return any(host == s or host.endswith(f".{s}") for s in self.allowed_suffixes)

    def _fetch_text(self, url: str) -> str:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ")).strip()

    @staticmethod
    def _title_from_url(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname or url

    @staticmethod
    def _load_allowed_suffixes() -> list[str]:
        env = os.environ.get(
            "ALLOWED_EXTERNAL_SUFFIXES",
            "go.kr,ac.kr,gov,edu,gov.cn,edu.cn,ac.uk,gov.uk",
        )
        return [x.strip().lower().lstrip(".") for x in env.split(",") if x.strip()]