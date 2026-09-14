"""
experiments/smoke_test_crawler.py
크롤러 스모크테스트 — uncovered 2개만 돌려 크롤러 로직 검증
(Ollama / GraphStore / RetrievalEngine 불필요 — 크롤러만 테스트)

대상:
  - v_uncov_1: 하이코리아 방문예약 (hikorea.go.kr)
  - h_uncov_3: 석당 글로벌하우스 퇴사 신청 (globalhouse.donga.ac.kr)

통과 기준: 둘 다 snippets 가 1개 이상 반환됨

실행:
  python experiments/smoke_test_crawler.py
"""
from __future__ import annotations

import os
import sys
from time import perf_counter

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

import requests
from openai import OpenAI

from yhs.infra.embedder import Embedder
from yhs.rag.crawler.web_search_client import WebSearchClient, allowed_sites

SMOKE_QUERIES = [
    {
        "id": "v_uncov_1",
        "query": "이번 학기 체류기간 연장 방문예약 언제까지 받아?",
        "source": "https://www.hikorea.go.kr/cvlappl/CvlapplStep1.pt",
    },
    {
        "id": "h_uncov_3",
        "query": "석당 글로벌하우스 이번 학기 퇴사(퇴소) 신청 마감일 언제야?",
        "source": "http://globalhouse.donga.ac.kr",
    },
]


def main() -> None:
    print("=" * 60)
    print("크롤러 스모크테스트 (OpenAI 링크선택, Ollama 불필요)")
    print("=" * 60)

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    embedder = Embedder()
    http = requests.Session()

    # llm=None, openai_client 주입 → 링크선택에 OpenAI 사용
    web_client = WebSearchClient(
        http=http,
        embedder=embedder,
        llm=None,
        driver=None,
        allowed_sites=allowed_sites,
        openai_client=openai_client,
    )

    results = []
    for q in SMOKE_QUERIES:
        qid = q["id"]
        question = q["query"]
        print(f"\n{'='*60}")
        print(f"[SMOKE] id={qid}")
        print(f"  질문: {question}")
        print(f"  source: {q['source']}")

        t0 = perf_counter()
        try:
            snippets = web_client.search_and_collect(question, max_results=3)
            latency = perf_counter() - t0
            has_web = bool(snippets)
            verdict = "PASS" if has_web else "FAIL"

            print(f"\n  [결과] snippets={len(snippets)}개, latency={latency:.1f}s")
            for i, sn in enumerate(snippets):
                print(f"    [{i}] {sn.url}")
                print(f"         {sn.snippet[:100]}")
            print(f"  → [{verdict}]")

            results.append({
                "id": qid,
                "has_web": has_web,
                "n_snippets": len(snippets),
                "latency": round(latency, 1),
                "verdict": verdict,
            })
        except Exception as exc:
            import traceback
            latency = perf_counter() - t0
            print(f"  [FATAL ERROR] {exc}")
            traceback.print_exc()
            results.append({"id": qid, "has_web": False, "verdict": "FAIL", "error": str(exc)})

    web_client.close()

    print("\n" + "=" * 60)
    print("스모크테스트 요약")
    print("=" * 60)
    all_pass = True
    for r in results:
        v = r.get("verdict", "FAIL")
        print(f"  {r['id']}: {v}  (snippets={r.get('n_snippets', 0)}, latency={r.get('latency', '?')}s)")
        if v != "PASS":
            all_pass = False

    if all_pass:
        print("\n전체 통과 — 전체 100개 실험으로 진행 가능.")
    else:
        print("\n일부 실패 — 원인 파악 후 전체 실험 진행 필요.")
        sys.exit(1)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    main()
