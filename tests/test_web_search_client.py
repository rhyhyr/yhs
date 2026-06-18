from __future__ import annotations

from agent.crawler.web_search_client import WebSearchClient


def test_crawl_fallback_chunks_visits_all_allowed_site_roots_first(monkeypatch):
    client = WebSearchClient.__new__(WebSearchClient)

    site_a = "https://site-a.example"
    site_b = "https://site-b.example"
    site_c = "https://site-c.example"
    client.ALLOWED_SITES = [site_a, site_b, site_c]

    visited_urls: list[str] = []

    def fake_fetch(url: str):
        visited_urls.append(url)
        if url == site_a:
            return "A root", [
                ("A-1", f"{site_a}/one"),
                ("A-2", f"{site_a}/two"),
            ]
        if url == site_b:
            return "B root", [("B-1", f"{site_b}/one")]
        if url == site_c:
            return "C root", [("C-1", f"{site_c}/one")]
        return f"{url} body", []

    client.fetch_page_links_and_text = fake_fetch
    client.llm_select_links = lambda query, links, visited, max_select=2: [url for _, url in links[:max_select]]
    client._chunk_text = lambda text, chunk_size=500, overlap=100: [text]

    monkeypatch.setattr("agent.crawler.web_search_client.CRAWL_MAX_PAGES", 3)
    monkeypatch.setattr("agent.crawler.web_search_client.CRAWL_MAX_DEPTH", 4)
    monkeypatch.setattr("agent.crawler.web_search_client.CRAWL_SLEEP_SEC", 0)

    chunks = client.crawl_fallback_chunks("테스트 질문")

    assert visited_urls[:3] == [site_a, site_b, site_c]
    assert {url for url, _ in chunks} == {site_a, site_b, site_c}
    assert len(chunks) == 3