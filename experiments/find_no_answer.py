# -*- coding: utf-8 -*-
import sys, os, io
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                                   # experiments.* 패키지
sys.path.insert(0, os.path.join(_ROOT, "backend", "src"))   # yhs.* 패키지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from yhs.rag.engine import RetrievalEngine
from yhs.infra.graph_store import GraphStore
from yhs.infra.embedder import Embedder
from experiments.eval_sets.eval_questions_v2 import EVAL_QUERIES

queries = [q for q in EVAL_QUERIES if q["lang"] == "ko" and q["stratum"] in ("in_db", "complex")]

embedder = Embedder()
with GraphStore() as store:
    engine = RetrievalEngine(store, embedder)
    print("=== no_answer 항목 ===")
    for q in queries:
        r = engine.retrieve(q["query"])
        best = max((c.score for c in r.chunks), default=0.0)
        chunks = len(r.chunks)
        if r.retrieval_method == "no_answer":
            print(f"NO_ANS | {q['id']:15s} | best={best:.3f} chunks={chunks} | {q['query']}")
        else:
            top_src = r.chunks[0].source_file if r.chunks else "?"
            print(f"OK     | {q['id']:15s} | best={best:.3f} chunks={chunks} | top_src={top_src[:40]}")
