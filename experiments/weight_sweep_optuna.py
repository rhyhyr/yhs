# -*- coding: utf-8 -*-
"""
experiments/weight_sweep_optuna.py

retrieval_engine.py 의 (_W_BASE, _W_KW, _W_REC) 가중치를 Optuna TPE로 최적화.

전략
-----
  Phase 1 (1회실행)
    모든 쿼리에 대해 entity link + 그래프/벡터 검색을 사전 계산해 캐싱.
    이 단계에서만 EXAONE(via Ollama) 호출이 발생.

  Phase 2 (n_trials회)
    가중치만 바꿔 _merge_and_rerank() 를 재실행 → gold recall 측정.
    LLM / DB 호출 없음 → trial당 수ms 수준으로 빠름.

목적함수
---------
  문자 바이그램 gold recall:
    gold 텍스트의 바이그램 집합 중 검색된 청크 텍스트에 포함된 비율 (0~1).
  in_db + complex 쿼리 평균. (uncovered/dirty 제외 — DB에 정답 없음)

사용법
------
  pip install optuna tqdm
  python experiments/weight_sweep_optuna.py [--trials 100]
"""

from __future__ import annotations

import argparse
import io
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("RUNTIME_LLM", "ollama")  # EXAONE3.5 via Ollama

from dotenv import load_dotenv
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=True)

import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

import yhs.rag.engine as re_module
from yhs.rag.engine import RetrievalEngine
from yhs.core.config import DEFAULT_HOP_DEPTH, TOP_K_GRAPH_DEFAULT
from yhs.infra.graph_store import GraphStore
from yhs.infra.embedder import Embedder
from experiments.eval_sets.eval_questions_v2 import EVAL_QUERIES

# in_db + complex 만 대상 (DB에 정답 청크가 존재하는 항목)
TARGET = [q for q in EVAL_QUERIES if q["stratum"] in ("in_db", "complex")]

# 현재(베이스라인) 가중치 — 스크립트 종료 시 복원용
_BASELINE = {"w_base": 0.60, "w_kw": 0.30, "w_rec": 0.10}


# ── 유사도 지표 ──────────────────────────────────────────────────────────────

def _char_bigrams(text: str) -> set[str]:
    """공백·개행 제거 후 문자 바이그램 집합 반환."""
    s = text.replace(" ", "").replace("\n", "")
    return {s[i : i + 2] for i in range(len(s) - 1)}


def gold_recall(gold: str, chunks: list[dict]) -> float:
    """gold 바이그램 중 검색 청크 텍스트에 포함된 비율 (0~1)."""
    gold_bg = _char_bigrams(gold)
    if not gold_bg:
        return 0.0
    chunk_text = "".join(c.get("text", "") for c in chunks)
    chunk_bg = _char_bigrams(chunk_text)
    return len(gold_bg & chunk_bg) / len(gold_bg)


# ── Phase 1: 원시 검색 결과 사전 계산 ───────────────────────────────────────

def precompute(engine: RetrievalEngine) -> list[dict]:
    """entity link + 그래프/벡터 검색을 전체 쿼리에 대해 1회 실행 후 캐싱."""
    cache: list[dict] = []
    for i, q in enumerate(TARGET, 1):
        print(f"  [{i:2d}/{len(TARGET)}] {q['id']}: {q['query'][:45]}…", flush=True)
        try:
            link_result = engine._linker.link(q["query"])
            anchors: list[str] = link_result.get("anchors", [])
            entity_ids: list[str] = link_result.get("entity_ids", [])

            triples, graph_chunks = [], []
            if entity_ids:
                triples, graph_chunks = engine._graph_retriever.retrieve(
                    entity_ids,
                    hop_depth=DEFAULT_HOP_DEPTH,
                    top_k=TOP_K_GRAPH_DEFAULT,
                )

            vector_chunks = engine._vector_retriever.search(
                q["query"],
                top_k=re_module._CANDIDATE_TOP_K,
                keywords=anchors,
            )
            routed_chunks = engine._fetch_source_routed_chunks(q["query"])

        except Exception as exc:
            print(f"    ⚠ 오류: {exc}", flush=True)
            triples, graph_chunks, vector_chunks, routed_chunks, anchors = [], [], [], [], []

        cache.append(
            {
                "id": q["id"],
                "gold": q["gold"],
                "query": q["query"],
                "stratum": q["stratum"],
                "graph_chunks": graph_chunks,
                "vector_chunks": vector_chunks,
                "routed_chunks": routed_chunks,
                "anchors": anchors,
                "triples": triples,
            }
        )
    return cache


# ── Phase 2: Optuna objective ────────────────────────────────────────────────

def make_objective(engine: RetrievalEngine, cache: list[dict]):
    """캐시된 원시 결과만으로 merge 재실행 → gold recall 반환."""

    def objective(trial: optuna.Trial) -> float:
        w_base = trial.suggest_float("w_base", 0.30, 0.85)
        w_kw   = trial.suggest_float("w_kw",   0.10, 0.60)

        # w_rec 가 너무 작아지는 조합 제외
        if w_base + w_kw > 0.95:
            raise optuna.TrialPruned()

        w_rec = 1.0 - w_base - w_kw

        # retrieval_engine 모듈 변수 패치 (call-time lookup이라 인스턴스 불필요)
        re_module._W_BASE = w_base
        re_module._W_KW   = w_kw
        re_module._W_REC  = w_rec

        recalls: list[float] = []
        for cached in cache:
            merged = engine._merge_and_rerank(
                cached["graph_chunks"],
                cached["vector_chunks"],
                cached["query"],
                cached["anchors"],
                routed_chunks=cached["routed_chunks"],
            )
            recalls.append(gold_recall(cached["gold"], merged))

        return sum(recalls) / len(recalls)

    return objective


# ── 결과 출력 ────────────────────────────────────────────────────────────────

def print_results(study: optuna.Study) -> None:
    best = study.best_trial
    w_base = best.params["w_base"]
    w_kw   = best.params["w_kw"]
    w_rec  = 1.0 - w_base - w_kw

    print("\n" + "=" * 65)
    print("Optuna 가중치 최적화 결과")
    print("=" * 65)
    print(f"  최적 gold recall : {best.value:.4f}")
    print(f"  _W_BASE = {w_base:.3f}   (베이스라인: {_BASELINE['w_base']})")
    print(f"  _W_KW   = {w_kw:.3f}   (베이스라인: {_BASELINE['w_kw']})")
    print(f"  _W_REC  = {w_rec:.3f}   (베이스라인: {_BASELINE['w_rec']})")

    print("\n상위 5 trial:")
    completed = [t for t in study.trials if t.value is not None]
    top5 = sorted(completed, key=lambda t: t.value, reverse=True)[:5]
    for t in top5:
        wb = t.params.get("w_base", 0)
        wk = t.params.get("w_kw", 0)
        wr = 1.0 - wb - wk
        print(
            f"  #{t.number:3d}  recall={t.value:.4f}"
            f"  w_base={wb:.3f}  w_kw={wk:.3f}  w_rec={wr:.3f}"
        )

    print("=" * 65)
    print("\n▶ retrieval_engine.py 적용 권장값:")
    print(f"  _W_BASE = {round(w_base, 2)}")
    print(f"  _W_KW   = {round(w_kw, 2)}")
    print(f"  _W_REC  = {round(w_rec, 2)}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Optuna 가중치 탐색")
    parser.add_argument("--trials", type=int, default=100, help="Optuna trial 수 (기본: 100)")
    args = parser.parse_args()

    print(f"대상 쿼리 : {len(TARGET)}개  (in_db + complex)")
    print(f"Optuna trials : {args.trials}")
    print(f"RUNTIME_LLM   : {os.environ.get('RUNTIME_LLM', 'ollama')}  (Phase 1 entity link 전용)\n")

    print("Embedder 로딩 중…")
    embedder = Embedder()

    with GraphStore() as store:
        engine = RetrievalEngine(store, embedder)

        print(f"Phase 1 — {len(TARGET)}개 쿼리 사전 검색 (EXAONE entity link 포함)…")
        cache = precompute(engine)
        print(f"  → 완료 ({len(cache)}개 캐시)\n")

        print(f"Phase 2 — Optuna TPE 탐색 ({args.trials} trials, LLM 없음)…")
        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(
            make_objective(engine, cache),
            n_trials=args.trials,
            show_progress_bar=True,
        )

    print_results(study)

    # 모듈 변수 베이스라인으로 복원
    re_module._W_BASE = _BASELINE["w_base"]
    re_module._W_KW   = _BASELINE["w_kw"]
    re_module._W_REC  = _BASELINE["w_rec"]


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    main()
