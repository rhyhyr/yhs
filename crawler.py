from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
from typing import Any, Optional

import numpy as np
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# ── 환경변수 (hybrid_query_agent.py와 공유) ───────────────────────────────
VEC_WEIGHT          = float(os.environ.get("VEC_WEIGHT", "0.62"))
KW_WEIGHT           = float(os.environ.get("KW_WEIGHT", "0.38"))
CRAWL_MAX_DEPTH     = int(os.environ.get("CRAWL_MAX_DEPTH", "3"))
CRAWL_MAX_PAGES     = int(os.environ.get("CRAWL_MAX_PAGES", "10"))
CRAWL_FETCH_TIMEOUT = int(os.environ.get("CRAWL_FETCH_TIMEOUT", "6"))
CRAWL_SLEEP_SEC     = float(os.environ.get("CRAWL_SLEEP_SEC", "0.15"))


class Crawler:
    """
    ALLOWED_SITES 내에서 Playwright(JS 렌더링) + Gemini LLM 가이드 방식으로
    질문과 관련 있는 페이지를 찾아 크롤링하는 클래스.

    [추가된 기능]
    - run_pipeline(query)  : 메뉴 수집 → URL 선택 → 페이지 크롤 → 답변 생성 4단계 파이프라인
    - crawl_page(url)      : 테이블 우선 Playwright 크롤러 (JS 렌더링 페이지 대응)
    - generate_answer(...) : Gemini 기반 최종 답변 생성
    """

    def __init__(
        self,
        http: requests.Session,
        embedder: Any,
        llm: Any,           # Gemini GenerativeModel (URL 선택 + 답변 생성 모두 사용)
        allowed_sites: list[str],
        driver: Any,        # Neo4j driver (save_external_chunks 용)
        openai_client: Any | None = None,
    ) -> None:
        self.http          = http
        self.embedder      = embedder
        self.llm           = llm
        self.openai_client = openai_client or self._build_openai_client()
        self.ALLOWED_SITES = allowed_sites
        self.driver        = driver

    # =========================================================================
    # 내부 유틸
    # =========================================================================

    def _tokens(self, text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"[가-힣A-Za-z0-9]{2,}", text)]

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

    def _gemini(self, prompt: str) -> str:
        """Gemini 호출 공통 헬퍼. llm이 None이면 빈 문자열 반환."""
        if self.llm is None:
            return ""
        try:
            resp = self.llm.generate_content(
                prompt,
                generation_config={"temperature": 0.0},
            )
            return (resp.text or "").strip()
        except Exception as e:
            print(f"[WARN] Gemini 호출 실패: {e}", flush=True)
            return ""

    def _build_openai_client(self) -> Any | None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            print("[WARN] OPENAI_API_KEY가 .env에 없어 OpenAI 클라이언트를 만들지 못했습니다.", flush=True)
            return None
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            print(f"[WARN] OpenAI client init failed: {e}", flush=True)
            return None

    def _openai_chat(self, messages: list[dict[str, str]], json_mode: bool = False) -> str:
        if self.openai_client is None:
            prompt = "\n\n".join(f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages)
            return self._gemini(prompt)
        try:
            kwargs: dict[str, Any] = {
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": messages,
                "temperature": 0,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = self.openai_client.chat.completions.create(**kwargs)
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[WARN] OpenAI 호출 실패: {e}", flush=True)
            return ""

    # =========================================================================
    # 페이지 fetch (기존)
    # =========================================================================

    def fetch_page_links_and_text(self, url: str) -> tuple[str, list[tuple[str, str]]]:
        """
        Playwright로 JS 렌더링 완료 후 페이지를 읽어옴.
        반환: (본문텍스트, [(메뉴경로>링크텍스트, 링크URL), ...])
        Playwright 미설치 시 requests로 폴백.
        """
        html = ""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=15000, wait_until="networkidle")
                html = page.content()
                browser.close()
        except ImportError:
            print("[WARN] Playwright 미설치 → requests 폴백.")
            try:
                r = self.http.get(url, timeout=CRAWL_FETCH_TIMEOUT)
                r.raise_for_status()
                html = r.text
            except Exception:
                return "", []
        except Exception as e:
            print(f"[WARN] Playwright 오류({e}) → requests 폴백")
            try:
                r = self.http.get(url, timeout=CRAWL_FETCH_TIMEOUT)
                r.raise_for_status()
                html = r.text
            except Exception:
                return "", []

        soup = BeautifulSoup(html, "html.parser")

        # 메뉴 구조 추출: 상위메뉴 > 하위메뉴 경로로 라벨 구성
        links: list[tuple[str, str]] = []
        seen_hrefs: set[str] = set()

        menu_roots = soup.select("nav, #gnb, #lnb, #snb, .gnb, .lnb, .nav, .menu, ul.depth1, ul.depth2")
        if not menu_roots:
            menu_roots = [soup]

        for root in menu_roots:
            for top_li in root.select("li"):
                top_label = ""
                top_a = top_li.find("a", recursive=False)
                if top_a:
                    top_label = top_a.get_text(strip=True)[:30]

                for a in top_li.select("a[href]"):
                    href = a.get("href", "").strip()
                    if not href or href.startswith("#") or href.startswith("javascript"):
                        continue
                    full_url = urllib.parse.urljoin(url, href).split("#")[0]
                    if not any(full_url.startswith(site) for site in self.ALLOWED_SITES):
                        continue
                    if full_url in seen_hrefs:
                        continue
                    seen_hrefs.add(full_url)
                    sub_label = a.get_text(strip=True)[:40]
                    if top_label and sub_label and top_label != sub_label:
                        label = f"{top_label} > {sub_label}"
                    else:
                        label = sub_label or top_label or full_url
                    links.append((label, full_url))

        # 메뉴에서 못 찾은 링크도 추가 수집
        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            full_url = urllib.parse.urljoin(url, href).split("#")[0]
            if not any(full_url.startswith(site) for site in self.ALLOWED_SITES):
                continue
            if full_url in seen_hrefs:
                continue
            seen_hrefs.add(full_url)
            label = a.get_text(strip=True)[:60] or full_url
            links.append((label, full_url))

        # 본문 텍스트 추출
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        txt = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        return txt[:6000], links

    def fetch_page_text(self, url: str) -> str:
        text, _ = self.fetch_page_links_and_text(url)
        return text

    # =========================================================================
    # LLM 링크 선택 (기존 - 복수 URL, crawl_fallback_chunks에서 사용)
    # =========================================================================

    def llm_select_links(
        self,
        query: str,
        links: list[tuple[str, str]],
        visited: set[str],
    ) -> list[str]:
        """
        Gemini가 메뉴 경로가 포함된 링크 목록을 보고 질문과 관련 있는 링크만 선택.
        최대 3개 반환. crawl_fallback_chunks 에서 사용.
        """
        links = [(label, url) for label, url in links if url not in visited]
        if not links:
            return []
        if self.openai_client is None:
            return [url for _, url in links[:5]]

        lines = [f"{i+1}. {label} → {url}" for i, (label, url) in enumerate(links[:40])]
        prompt = (
            "다음은 대학교 홈페이지의 메뉴 구조입니다. (형식: 상위메뉴 > 하위메뉴 → URL)\n"
            "아래 질문에 답하기 위해 들어가봐야 할 메뉴의 번호만 골라 콤마로 나열하세요.\n"
            "최대 3개만 선택하고, 설명 없이 번호만 반환하세요.\n"
            "예시 출력: 2,5\n\n"
            f"질문: {query}\n\n"
            "메뉴 목록:\n" + "\n".join(lines)
        )
        text = self._openai_chat([
            {
                "role": "system",
                "content": "대학 홈페이지 메뉴에서 질문과 관련된 링크 번호만 콤마로 반환하세요. 설명은 금지합니다.",
            },
            {"role": "user", "content": prompt},
        ])
        if not text:
            return [url for _, url in links[:3]]

        picked_nums = [x.strip() for x in re.split(r"[,\n]", text) if x.strip().isdigit()]
        selected_urls = []
        for num in picked_nums:
            idx = int(num) - 1
            if 0 <= idx < len(links):
                selected_urls.append(links[idx][1])
        print(
            f"[CRAWL] LLM 선택 메뉴: "
            f"{[links[int(n)-1][0] for n in picked_nums if n.isdigit() and 0 <= int(n)-1 < len(links)]}",
            flush=True,
        )
        return selected_urls or [url for _, url in links[:3]]

    # =========================================================================
    # [추가] run_pipeline 전용 - 단일 최적 URL 선택 (Gemini)
    # =========================================================================

    def _llm_select_single_url(
        self,
        query: str,
        links: list[tuple[str, str]],
    ) -> dict:
        """
        run_pipeline에서 사용. 질문에 가장 맞는 URL 딱 1개를 Gemini로 선택.
        반환: {"text": str, "url": str, "reason": str}
        """
        lines = "\n".join(
            f"{i+1}. [{label}] {url}"
            for i, (label, url) in enumerate(links)
        )
        prompt = (
            "당신은 대학교 홈페이지 URL 선택 전문가입니다.\n"
            "사용자 질문에 답하기 위해 크롤링해야 할 URL을 딱 하나만 골라서 "
            "반드시 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 출력하지 마세요.\n"
            '출력 형식: {"index": 숫자, "text": "메뉴명", "url": "URL", "reason": "선택이유"}\n\n'
            f"질문: {query}\n\n"
            f"링크 목록:\n{lines}"
        )
        raw = self._openai_chat(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 대학교 홈페이지 URL 선택 전문가입니다. "
                        "사용자 질문에 답하기 위해 크롤링해야 할 URL을 하나만 골라 JSON 형식으로만 응답하세요."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            json_mode=True,
        )
        raw = re.sub(r"```json|```", "", raw).strip()

        try:
            return json.loads(raw)
        except Exception:
            label, url = links[0]
            print(f"[WARN] URL 선택 JSON 파싱 실패 → 첫 번째 링크 사용: {url}", flush=True)
            return {"text": label, "url": url, "reason": "JSON 파싱 실패 - 폴백"}

    # =========================================================================
    # [추가] crawl_page - 테이블 우선 Playwright 크롤러
    # =========================================================================

    def crawl_page(self, url: str) -> str:
        """
        Playwright로 페이지를 열고 본문을 추출.
        우선순위:
          1) <table> 존재 → 테이블 텍스트  (학사일정, 공지사항 등 표 형태)
          2) 본문 셀렉터   → #container / #content / main / article 순서
          3) body 전체    → 최후 수단
        """
        print(f"[STEP 3] Playwright 크롤링: {url}", flush=True)

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=15000, wait_until="networkidle")
                page.wait_for_timeout(1000)

                # 1순위: 테이블
                table_el = page.query_selector("table")
                if table_el:
                    content = table_el.inner_text()
                    print("[STEP 3] 테이블 감지 → 테이블 텍스트 추출", flush=True)
                else:
                    content = ""
                    for selector in ["#container", "#content", ".content-wrap", "main", "article"]:
                        el = page.query_selector(selector)
                        if el:
                            content = el.inner_text()
                            print(f"[STEP 3] '{selector}' 본문 영역 추출", flush=True)
                            break
                    if not content:
                        content = page.inner_text("body")
                        print("[STEP 3] body 전체 추출 (폴백)", flush=True)

                browser.close()

        except Exception as e:
            print(f"[WARN] crawl_page 오류({e}) → fetch_page_text 폴백", flush=True)
            content = self.fetch_page_text(url)

        lines = [l.strip() for l in content.split("\n") if l.strip()]
        content = "\n".join(lines)

        print(f"[STEP 3] 완료: {len(content)}bytes", flush=True)
        print("\n=== 크롤링 결과 앞 100자 ===")
        print(content[:100])
        print("============================\n")

        return content

    # =========================================================================
    # [추가] generate_answer - Gemini로 최종 답변 생성
    # =========================================================================

    def generate_answer(self, query: str, content: str, source_url: str) -> str:
        """크롤링한 페이지 내용을 근거로 Gemini가 답변 생성."""
        print("[STEP 4] OpenAI 답변 생성 중...", flush=True)

        if not self.openai_client:
            return "LLM이 설정되지 않아 답변을 생성할 수 없습니다."

        prompt = (
            "당신은 동아대학교 유학생을 돕는 AI 어시스턴트입니다.\n"
            "아래 제공된 학교 홈페이지 내용만을 근거로 답변하세요.\n"
            "내용에 없는 정보는 절대 추측하지 마세요.\n"
            "답변은 한국어로 작성하고, 마지막에 영어 번역도 함께 제공하세요.\n"
            "친절하고 간결하게 핵심만 말해주세요.\n\n"
            f"질문: {query}\n\n"
            f"[출처: {source_url}]\n\n"
            f"{content[:6000]}"
        )

        answer = self._openai_chat([
            {
                "role": "system",
                "content": (
                    "당신은 동아대학교 유학생을 돕는 AI 어시스턴트입니다.\n"
                    "아래 제공된 학교 홈페이지 내용만을 근거로 답변하세요.\n"
                    "내용에 없는 정보는 절대 추측하지 마세요.\n"
                    "답변은 한국어로 작성하고, 마지막에 영어 번역도 함께 제공하세요.\n"
                    "친절하고 간결하게 핵심만 말해주세요."
                ),
            },
            {"role": "user", "content": prompt},
        ])
        if not answer:
            answer = "답변을 생성하지 못했습니다."

        print("[STEP 4] 완료", flush=True)
        return answer

    # =========================================================================
    # [추가] run_pipeline - 4단계 파이프라인 (질문 → 최종 답변)
    # =========================================================================

    # 링크 수집 시작점: 메인 홈페이지 (crawl_test.py와 동일)
    _PIPELINE_BASE_URL = "https://www.donga.ac.kr"

    def run_pipeline(self, query: str) -> str:
        print("=" * 60, flush=True)
        print(f"[PIPELINE] 질문: {query}", flush=True)
        print("=" * 60, flush=True)

        # ── STEP 1. crawl_test.py와 동일한 방식으로 링크 수집 ────────
        print("[STEP 1] 메뉴 링크 수집 중...", flush=True)
        base_url = self._PIPELINE_BASE_URL  # 전체 메뉴가 있는 메인 홈페이지
        links = []

        try:
            from playwright.sync_api import sync_playwright
            import urllib.parse
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(base_url, timeout=15000, wait_until="networkidle")
                seen = set()
                for a in page.query_selector_all("a[href]"):
                    try:
                        text = a.inner_text().strip()
                        href = a.get_attribute("href") or ""
                        if not href or href.startswith("#") or not text:
                            continue
                        full_url = href if href.startswith("http") else urllib.parse.urljoin(base_url, href)
                        if full_url not in seen:
                            seen.add(full_url)
                            links.append((text, full_url))  # tuple 형태로 저장
                    except:
                        continue
                browser.close()
        except Exception as e:
            print(f"[WARN] Playwright 링크 수집 실패: {e}", flush=True)
            _, links = self.fetch_page_links_and_text(base_url)  # 폴백

        print(f"[STEP 1] 완료: {len(links)}개 링크 수집", flush=True)

        if not links:
            return "홈페이지에서 링크를 수집하지 못했습니다."

        # ── STEP 2, 3, 4 기존과 동일 ─────────────────────────────────
        print("[STEP 2] OpenAI가 URL 선택 중...", flush=True)
        selected = self._llm_select_single_url(query, links)
        print(f"[STEP 2] 선택: [{selected['text']}] {selected['url']}", flush=True)
        print(f"[STEP 2] 이유: {selected['reason']}", flush=True)

        content = self.crawl_page(selected["url"])
        if not content:
            return "페이지 내용을 가져오지 못했습니다."

        answer = self.generate_answer(query, content, selected["url"])

        print("\n" + "=" * 60, flush=True)
        print("[PIPELINE] 최종 답변", flush=True)
        print("=" * 60, flush=True)
        print(answer, flush=True)

        return answer

    # =========================================================================
    # 메인 크롤링 (기존 - crawl_fallback_chunks)
    # =========================================================================

    def crawl_fallback_chunks(self, query: str) -> list[tuple[str, str]]:
        """
        Playwright로 JS 렌더링 후 메뉴 구조를 파악,
        Gemini가 질문과 관련 있는 메뉴를 선택해 타고 들어가는 방식으로 크롤링.
        """
        all_chunks: list[tuple[str, str]] = []
        visited: set[str] = set()
        total_pages = 0

        for base_url in self.ALLOWED_SITES:
            if total_pages >= CRAWL_MAX_PAGES:
                break

            queue: list[tuple[str, int]] = [(base_url, 0)]

            while queue and total_pages < CRAWL_MAX_PAGES:
                current_url, depth = queue.pop(0)

                if current_url in visited:
                    continue
                visited.add(current_url)
                total_pages += 1

                print(f"[CRAWL] depth={depth} 방문: {current_url}", flush=True)
                page_text, links = self.fetch_page_links_and_text(current_url)
                time.sleep(CRAWL_SLEEP_SEC)

                if page_text:
                    for chunk in self._chunk_text(page_text):
                        all_chunks.append((current_url, chunk))

                if depth >= CRAWL_MAX_DEPTH:
                    continue

                if links:
                    selected_urls = self.llm_select_links(query, links, visited)
                    for next_url in selected_urls:
                        if next_url not in visited:
                            queue.append((next_url, depth + 1))

        return all_chunks

    # =========================================================================
    # 스코어링 / 저장 (기존)
    # =========================================================================

    def score_external_chunks(
        self,
        query: str,
        query_emb: np.ndarray,
        url_chunks: list[tuple[str, str]],
    ) -> list[tuple[str, str, float]]:
        if not url_chunks:
            return []
        embs = self.embedder.encode([c for _, c in url_chunks], show_progress_bar=False)
        out: list[tuple[str, str, float]] = []
        for (u, c), e in zip(url_chunks, embs):
            vec = float(cosine_similarity([query_emb], [e])[0][0])
            kw  = self._kw_score(query, c)
            score = VEC_WEIGHT * vec + KW_WEIGHT * kw
            out.append((u, c, score))
        out.sort(key=lambda x: x[2], reverse=True)
        return out

    def save_external_chunks(self, url_chunks: list[tuple[str, str]]) -> None:
        """크롤링 결과를 Neo4j ExternalChunk 노드로 저장"""
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