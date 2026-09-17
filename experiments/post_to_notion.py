"""
experiments/post_to_notion.py
uncovered 실험 결과를 Notion 페이지에 기록

실행: python experiments/post_to_notion.py
"""
from __future__ import annotations

import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지
from dotenv import load_dotenv

load_dotenv()

import requests

NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
NOTION_PAGE_ID = os.environ["NOTION_PAGE_ID"]
RUNS_PATH      = "experiments/results/runs_uncovered.jsonl"
SCORES_PATH    = "experiments/results/scores_uncovered.jsonl"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _text(content: str, bold=False, color="default") -> dict:
    ann = {"bold": bold, "color": color}
    return {"type": "text", "text": {"content": content}, "annotations": ann}


def _heading(text: str, level: int = 2) -> dict:
    return {
        "object": "block",
        "type": f"heading_{level}",
        f"heading_{level}": {"rich_text": [_text(text, bold=True)]},
    }


def _paragraph(text: str, bold=False, color="default") -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [_text(text, bold=bold, color=color)]},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _table_row(cells: list[str]) -> dict:
    return {
        "type": "table_row",
        "table_row": {
            "cells": [[_text(c)] for c in cells]
        },
    }


def _table(headers: list[str], rows: list[list[str]]) -> dict:
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [_table_row(headers)] + [_table_row(r) for r in rows],
        },
    }


def _callout(text: str, emoji: str = "📊") -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [_text(text)],
            "icon": {"type": "emoji", "emoji": emoji},
            "color": "blue_background",
        },
    }


def create_page(parent_id: str, title: str, blocks: list[dict]) -> str:
    """부모 페이지 아래 새 페이지를 생성하고 page_id 반환."""
    url = "https://api.notion.com/v1/pages"
    # Notion API: children은 100개씩 나눠야 하므로 첫 100개만 생성 시 포함
    first_chunk = blocks[:100]
    body = {
        "parent": {"page_id": parent_id},
        "icon": {"type": "emoji", "emoji": "🧪"},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": first_chunk,
    }
    resp = requests.post(url, headers=HEADERS, json=body)
    if resp.status_code not in (200, 201):
        print(f"[ERROR] 페이지 생성 실패 {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)
    page_id = resp.json()["id"]
    print(f"[OK] 새 페이지 생성: {page_id}")

    # 나머지 블록 추가
    if len(blocks) > 100:
        append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        for i in range(100, len(blocks), 100):
            chunk = blocks[i:i+100]
            resp2 = requests.patch(append_url, headers=HEADERS, json={"children": chunk})
            if resp2.status_code not in (200, 201):
                print(f"[ERROR] 블록 추가 실패: {resp2.text[:300]}")
            time.sleep(0.3)

    print(f"[OK] 총 {len(blocks)}개 블록 기록 완료")
    return page_id


def main() -> None:
    runs   = [json.loads(l) for l in open(RUNS_PATH,   encoding="utf-8")]
    scores = [json.loads(l) for l in open(SCORES_PATH, encoding="utf-8")]
    score_map = {s["id"]: s for s in scores}

    qualities = [s.get("quality", 0) for s in scores if s.get("quality") is not None]
    avg_quality = sum(qualities) / len(qualities) if qualities else 0
    final_score = avg_quality / 5 * 100

    grounded_count = sum(1 for s in scores if s.get("grounded") == "Y")
    halluc_count   = sum(1 for s in scores if s.get("hallucination") == "Y")

    latencies = [r.get("latency", 0) for r in runs if r.get("latency")]
    latencies.sort()
    p50 = latencies[len(latencies)//2] if latencies else 0
    p95 = latencies[int(len(latencies)*0.95)] if latencies else 0

    # Build blocks
    blocks: list[dict] = []
    blocks.append(_divider())
    blocks.append(_heading("YHS 크롤러 실험 — uncovered 20개", level=2))
    blocks.append(_paragraph(f"측정일: {time.strftime('%Y-%m-%d')}  |  답변 모델: gpt-4o-mini  |  크롤 예산: 50페이지"))

    # Score rubric
    blocks.append(_heading("최종 점수 — 어떻게 산출했나", level=3))
    blocks.append(_paragraph("심판 모델(gpt-4o-mini)이 각 답변을 3개 항목으로 0~5점 채점"))
    blocks.append(_table(
        ["항목", "의미"],
        [
            ["accuracy",     "정답 근거와 사실 일치 정도"],
            ["relevance",    "질문에 직접·같은 언어로 답변"],
            ["completeness", "핵심 항목 누락 없이 답변"],
        ]
    ))
    blocks.append(_paragraph("최종 점수 = (accuracy + relevance + completeness) / 3 × 20  →  0~100점", bold=True))

    # Summary callout
    blocks.append(_callout(
        f"답변 품질: {avg_quality:.2f} / 5.0  →  {final_score:.1f}점 / 100점\n"
        f"근거 적합률: {grounded_count/len(scores)*100:.1f}%   환각률: {halluc_count/len(scores)*100:.1f}%\n"
        f"지연 p50/p95: {p50:.1f}s / {p95:.1f}s",
        emoji="📊"
    ))

    # Per-question table
    blocks.append(_heading("질문별 결과", level=3))
    table_rows = []
    for r in runs:
        s = score_map.get(r["id"], {})
        acc  = str(s.get("accuracy",     "—"))
        rel  = str(s.get("relevance",    "—"))
        comp = str(s.get("completeness", "—"))
        qual = str(s.get("quality",      "—"))
        answer_preview = r.get("answer", "")[:60].replace("\n", " ")
        table_rows.append([
            r["id"],
            r["query"][:35],
            acc, rel, comp, qual,
            answer_preview,
        ])

    blocks.append(_table(
        ["id", "query", "accuracy", "relevance", "completeness", "quality(avg)", "answer 미리보기"],
        table_rows,
    ))

    # Analysis
    blocks.append(_heading("분석", level=3))
    success = [r for r in runs if r.get("answer", "") and "확인할 수 없습니다" not in r.get("answer", "")]
    blocks.append(_paragraph(
        f"유의미한 답변: {len(success)}/20개\n"
        f"주요 실패 원인: '이번 학기/이번 달/이번 주' 실시간 공지를 크롤러가 depth {os.environ.get('CRAWL_MAX_DEPTH','4')}에서 미도달\n"
        f"환각률 {halluc_count/len(scores)*100:.0f}% — 모르는 경우 정직하게 '확인할 수 없습니다' 응답"
    ))

    title = f"YHS uncovered 실험 결과 — {time.strftime('%Y-%m-%d')} (크롤 50페이지)"
    new_page_id = create_page(NOTION_PAGE_ID, title, blocks)
    print("\n노션 새 페이지 생성 완료!")
    print(f"https://app.notion.com/p/d-{new_page_id.replace('-', '')}")


if __name__ == "__main__":
    main()
