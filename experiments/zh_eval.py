"""
experiments/zh_eval.py

중국어 질문 번역 레이어 성능 비교 실험

실행 방법:
    # 번역 ON (개선 후)
    python -m experiments.zh_eval

    # 번역 OFF (개선 전 시뮬레이션)
    ENABLE_ZH_TRANSLATION=false python -m experiments.zh_eval

    # 양쪽 한 번에 비교
    python -m experiments.zh_eval --compare

측정 지표:
    - intent_hit   : 의도 분류 성공 여부 (intents 리스트가 비어있지 않으면 성공)
    - entity_count : 링킹된 Entity 수 (그래프 탐색 시작점 수)
    - answer_found : retrieval_method != "no_answer"
    - method       : graph / vector / hybrid / no_answer
"""

from __future__ import annotations

import os
import sys
import json
import time
import argparse
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional

# ── 테스트 질문 셋 ────────────────────────────────────────────────────────────
# 실제 중국인 유학생이 쓸 법한 표현으로 작성
# 각 카테고리(intent)별로 2개씩 구성
ZH_TEST_QUERIES = [
    # visa
    {"id": "zh_v1", "query": "我的D-2签证怎么延长？需要什么材料？", "expected_intent": "visa"},
    {"id": "zh_v2", "query": "签证快到期了，去哪里办延期手续？", "expected_intent": "visa"},
    # arc
    {"id": "zh_a1", "query": "外国人登录证丢了怎么补办？", "expected_intent": "arc"},
    {"id": "zh_a2", "query": "我需要申请外国人登录证，去哪里办？", "expected_intent": "arc"},
    # health_insurance
    {"id": "zh_h1", "query": "留学生必须加入健康保险吗？", "expected_intent": "health_insurance"},
    {"id": "zh_h2", "query": "健康保险费用怎么交？", "expected_intent": "health_insurance"},
    # academic
    {"id": "zh_ac1", "query": "我想申请休学，需要提交什么材料？", "expected_intent": "academic"},
    {"id": "zh_ac2", "query": "选课申请是什么时候？怎么操作？", "expected_intent": "academic"},
    # dormitory
    {"id": "zh_d1", "query": "学校宿舍怎么申请？有什么条件？", "expected_intent": "dormitory"},
    {"id": "zh_d2", "query": "宿舍费用是多少？", "expected_intent": "dormitory"},
    # life_admin
    {"id": "zh_l1", "query": "留学生可以打工吗？一周最多几个小时？", "expected_intent": "life_admin"},
    {"id": "zh_l2", "query": "地址变更去哪里办理？", "expected_intent": "life_admin"},
]


@dataclass
class EvalResult:
    query_id: str
    query: str
    expected_intent: str
    translated: Optional[str]        # 번역된 텍스트 (번역 OFF면 None)
    intents: list
    entity_count: int
    retrieval_method: str
    intent_hit: bool                 # expected_intent가 intents 안에 있으면 True
    answer_found: bool               # no_answer가 아니면 True
    elapsed_sec: float


# ── 단일 질문 평가 ────────────────────────────────────────────────────────────
def evaluate_one(query_id: str, query: str, expected_intent: str) -> EvalResult:
    """
    질문 하나를 파이프라인에 넣고 결과를 반환한다.
    Neo4j 연결이 없어도 linker 단계(번역 + 의도분류 + entity linking)까지는 측정 가능.
    """
    from agent.retrieval.linker import EntityLinker, _classify_intent, _extract_anchors
    from agent.retrieval.translator import get_translator, is_translation_enabled

    start = time.perf_counter()

    # 번역 단계
    translator = get_translator()
    if is_translation_enabled():
        translated_text, was_translated = translator.translate_if_needed(query)
    else:
        translated_text, was_translated = query, False

    # 의도 분류 (번역 ON이면 번역된 텍스트, OFF면 원문)
    classify_target = translated_text if is_translation_enabled() else query
    intents = _classify_intent(classify_target)
    anchors = _extract_anchors(intents)

    elapsed = time.perf_counter() - start

    # entity linking & retrieval은 Neo4j 필요 → 연결 실패 시 linker 단계만 평가
    entity_count = 0
    retrieval_method = "not_tested"
    try:
        from graph_rag.db.graph_store import GraphStore
        from graph_rag.embedding.embedder import Embedder
        from graph_rag.config import (
            NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE,
            EMBEDDING_MODEL
        )
        from agent.retrieval_engine import RetrievalEngine

        store = GraphStore(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
        embedder = Embedder(EMBEDDING_MODEL)
        engine = RetrievalEngine(store, embedder)

        result = engine.retrieve(classify_target)
        entity_count = len(result.entity_ids)
        retrieval_method = result.retrieval_method

        elapsed = time.perf_counter() - start
    except Exception as e:
        # Neo4j 없으면 linker 단계만으로 평가
        retrieval_method = "db_unavailable"

    return EvalResult(
        query_id=query_id,
        query=query,
        expected_intent=expected_intent,
        translated=translated_text if was_translated else None,
        intents=intents,
        entity_count=entity_count,
        retrieval_method=retrieval_method,
        intent_hit=expected_intent in intents,
        answer_found=retrieval_method not in ("no_answer", "db_unavailable", "not_tested"),
        elapsed_sec=round(elapsed, 3),
    )


# ── 전체 평가 실행 ────────────────────────────────────────────────────────────
def run_eval(label: str) -> list[EvalResult]:
    translation_status = "ON" if os.getenv("ENABLE_ZH_TRANSLATION", "true").lower() != "false" else "OFF"
    print(f"\n{'='*60}")
    print(f"  {label}  (번역: {translation_status})")
    print(f"{'='*60}")

    results = []
    for q in ZH_TEST_QUERIES:
        r = evaluate_one(q["id"], q["query"], q["expected_intent"])
        intent_mark = "✓" if r.intent_hit else "✗"
        print(
            f"  [{intent_mark}] {r.query_id} | intent={r.intents or '[]'} "
            f"| method={r.retrieval_method} | {r.elapsed_sec}s"
        )
        if r.translated:
            print(f"       번역: {r.translated[:60]}")
        results.append(r)

    return results


# ── 리포트 출력 ───────────────────────────────────────────────────────────────
def print_report(label: str, results: list[EvalResult]) -> dict:
    total = len(results)
    intent_hits = sum(1 for r in results if r.intent_hit)
    answer_found = sum(1 for r in results if r.answer_found)
    avg_entities = sum(r.entity_count for r in results) / total
    avg_time = sum(r.elapsed_sec for r in results) / total

    summary = {
        "label": label,
        "total": total,
        "intent_hit_rate": f"{intent_hits / total * 100:.0f}%",
        "answer_found_rate": f"{answer_found / total * 100:.0f}%",
        "avg_entity_count": round(avg_entities, 2),
        "avg_elapsed_sec": round(avg_time, 3),
    }

    print(f"\n  ▶ 의도 분류 성공률 : {summary['intent_hit_rate']}  ({intent_hits}/{total})")
    print(f"  ▶ 답변 성공률       : {summary['answer_found_rate']}  ({answer_found}/{total})")
    print(f"  ▶ 평균 엔티티 수    : {summary['avg_entity_count']}")
    print(f"  ▶ 평균 처리 시간    : {summary['avg_elapsed_sec']}s")
    return summary


# ── --compare 모드: 두 번 실행해서 나란히 비교 ───────────────────────────────
def run_compare() -> None:
    """
    번역 OFF(이전) → 번역 ON(이후) 순으로 실행해서 결과를 비교한다.
    subprocess로 환경변수를 바꿔 각각 실행한다.
    """
    print("\n[ 번역 OFF (개선 전) ]")
    env_off = {**os.environ, "ENABLE_ZH_TRANSLATION": "false"}
    proc_off = subprocess.run(
        [sys.executable, "-m", "experiments.zh_eval", "--json"],
        capture_output=True, text=True, env=env_off,
    )
    before = json.loads(proc_off.stdout)

    print("\n[ 번역 ON (개선 후) ]")
    env_on = {**os.environ, "ENABLE_ZH_TRANSLATION": "true"}
    proc_on = subprocess.run(
        [sys.executable, "-m", "experiments.zh_eval", "--json"],
        capture_output=True, text=True, env=env_on,
    )
    after = json.loads(proc_on.stdout)

    # 비교 테이블 출력
    print(f"\n{'='*60}")
    print("  비교 결과")
    print(f"{'='*60}")
    print(f"  {'지표':<22} {'개선 전 (번역 OFF)':>18} {'개선 후 (번역 ON)':>17}")
    print(f"  {'-'*58}")

    metrics = [
        ("의도 분류 성공률", "intent_hit_rate"),
        ("답변 성공률",      "answer_found_rate"),
        ("평균 엔티티 수",   "avg_entity_count"),
        ("평균 처리 시간",   "avg_elapsed_sec"),
    ]
    for label, key in metrics:
        b = before.get(key, "-")
        a = after.get(key, "-")
        arrow = " ↑" if key in ("intent_hit_rate", "answer_found_rate", "avg_entity_count") else " ↓"
        print(f"  {label:<22} {str(b):>18} {str(a):>15}{arrow}")


# ── 진입점 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="중국어 번역 레이어 성능 평가")
    parser.add_argument("--compare", action="store_true", help="번역 ON/OFF 비교 실행")
    parser.add_argument("--json", action="store_true", help="요약을 JSON으로 출력 (내부 사용)")
    args = parser.parse_args()

    if args.compare:
        run_compare()
    else:
        label = "번역 ON" if os.getenv("ENABLE_ZH_TRANSLATION", "true").lower() != "false" else "번역 OFF"
        results = run_eval(label)
        summary = print_report(label, results)
        if args.json:
            print(json.dumps(summary, ensure_ascii=False))
