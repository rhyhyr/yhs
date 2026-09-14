"""
test_hf_local.py

HFRuntimeClient (EXAONE-3.5-2.4B-Instruct) 단독 테스트.
- Neo4j 없이 LLM 생성만 검증
- 이후 Neo4j가 켜져 있으면 Full Deep-Path 쿼리까지 실행

실행:
    python test_hf_local.py
"""
from __future__ import annotations

import os
import sys
import time

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("RUNTIME_LLM", "hf")
os.environ.setdefault("HF_RUNTIME_MODEL", "Qwen/Qwen2.5-3B-Instruct")

SAMPLE_CONTEXT = """
[비자연장 안내 | 2024.03 | p.4]
D-2(유학) 비자 체류기간 연장은 만료일 60일 전부터 신청 가능합니다.
신청 기관: 체류지 관할 출입국·외국인청
필요 서류: 여권, 외국인등록증, 재학증명서, 표준규격사진 1매, 수수료
건강보험 미납 시 연장이 거부될 수 있으므로 사전에 납부 내역을 확인하세요.
"""

TEST_QUESTIONS = [
    # Fast path (단순)
    "D-2 비자 연장 신청은 언제부터 할 수 있나요?",
    # Deep path 유도 (비교형)
    "D-2 비자와 D-4 비자의 차이점과 각각 연장 절차를 비교해 주세요.",
]


# ─── 단계 1: GPU/환경 확인 ────────────────────────────────────────────────────
def check_env() -> None:
    print("=" * 60)
    print("  환경 확인")
    print("=" * 60)
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"  GPU : {torch.cuda.get_device_name(0)}  ({vram:.1f} GB VRAM)")
        else:
            print("  GPU : 없음 (CPU 모드 — 매우 느릴 수 있음)")
    except ImportError:
        print("  [WARN] torch 미설치")

    try:
        import transformers
        print(f"  transformers : {transformers.__version__}")
    except ImportError:
        print("  [ERROR] transformers 미설치 → pip install transformers accelerate")
        sys.exit(1)
    print()


# ─── 단계 2: HFRuntimeClient LLM 생성 테스트 ─────────────────────────────────
def test_llm_generation() -> "HFRuntimeClient":
    from agent.hf_runtime_client import HFRuntimeClient
    from graph_rag.schema.types import RetrievalResult

    print("=" * 60)
    print("  LLM 생성 테스트 (모델 최초 로드 포함)")
    print("=" * 60)

    client = HFRuntimeClient()
    dummy_result = RetrievalResult(triples=[], chunks=[], retrieval_method="vector", entity_ids=[])

    for i, question in enumerate(TEST_QUESTIONS):
        print(f"\n[Q{i+1}] {question}")
        t0 = time.perf_counter()
        answer = client.generate_answer(
            question=question,
            context=SAMPLE_CONTEXT,
            result=dummy_result,
        )
        elapsed = time.perf_counter() - t0

        print(f"[A{i+1}] ({elapsed:.1f}s)")
        print(answer)
        print("-" * 50)

    return client


# ─── 단계 3: Full Deep-Path 테스트 (Neo4j 필요) ──────────────────────────────
def test_full_deep_path() -> None:
    print("\n" + "=" * 60)
    print("  Full Deep-Path 테스트 (Neo4j 연결 확인 중...)")
    print("=" * 60)

    try:
        from graph_rag.db.graph_store import GraphStore
        with GraphStore() as store:
            pass  # 연결 성공 여부만 확인
    except Exception as exc:
        print(f"  [SKIP] Neo4j 연결 실패 → {exc}")
        print("  Neo4j를 실행한 뒤 다시 시도하세요.")
        return

    print("  Neo4j 연결 성공 → 딥서치 쿼리 실행\n")

    # 비교형 질문 → Deep Path 강제 유도
    deep_question = "D-2 비자와 D-4 비자의 차이점과 각각 연장 절차를 비교해 주세요."

    from graph_rag.db.graph_store import GraphStore
    from graph_rag.embedding.embedder import Embedder
    from agent.hf_runtime_client import HFRuntimeClient
    from agent.retrieval_engine import RetrievalEngine
    from agent.agent_runtime import (
        GateThresholds, detect_language, detect_question_type,
        expand_query, should_use_deep_path, build_answer_prompt,
    )

    embedder = Embedder()
    llm = HFRuntimeClient()
    thresholds = GateThresholds.from_env()

    t_total = time.perf_counter()
    with GraphStore() as store:
        engine = RetrievalEngine(store, embedder)

        lang = detect_language(deep_question)
        q_type = detect_question_type(deep_question)
        print(f"  언어={lang}, 질문유형={q_type.value}")

        # Fast path
        t0 = time.perf_counter()
        result = engine.retrieve(deep_question)
        t_fast = time.perf_counter() - t0
        best = max((c.score for c in result.chunks), default=0.0)
        print(f"  [FAST] {t_fast:.2f}s | method={result.retrieval_method} | chunks={len(result.chunks)} | best={best:.3f}")

        # Deep path 판정
        use_deep, reasons = should_use_deep_path(deep_question, best, len(result.chunks), thresholds)
        print(f"  [GATE] use_deep={use_deep} reasons={reasons}")

        if use_deep:
            t0 = time.perf_counter()
            variants = expand_query(deep_question, lang)[1:]
            from graph_rag.schema.types import ChunkNode
            from agent.query_runner import _merge_results
            extra = []
            for v in variants:
                r = engine.retrieve(v)
                if r.retrieval_method != "no_answer":
                    extra.append(r)
            if extra:
                result = _merge_results(result, extra)
            t_deep = time.perf_counter() - t0
            print(f"  [DEEP] {t_deep:.2f}s | variants={len(variants)} | merged_chunks={len(result.chunks)}")

        # 답변 생성
        context = engine.build_prompt_context(result)
        if not context:
            context = "(검색 결과 없음)"

        t0 = time.perf_counter()
        answer = llm.generate_answer(deep_question, context, result)
        t_llm = time.perf_counter() - t0

        total = time.perf_counter() - t_total
        print(f"\n  LLM 생성: {t_llm:.1f}s | 전체: {total:.1f}s")
        print("\n[최종 답변]")
        print(answer)


# ─── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    check_env()
    test_llm_generation()
    test_full_deep_path()
    print("\n[완료] 테스트 성공")
