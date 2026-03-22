"""단일 PDF 인덱싱 모듈.

역할:
- 문서 1개를 받아 doc_key 중복 체크
- 카테고리/청크 임베딩 계산
- 청크를 하위 카테고리에 매핑해 Neo4j에 저장
"""

from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .categorizer import CategoryExtractor
from .config import SIM_THRESHOLD
from .models import CategoryNode
from .parser import PDFParser
from .store import Neo4jConnector


class Indexer:
    """단일 PDF를 계층 그래프로 변환해 저장하는 핵심 오케스트레이터."""
    def __init__(self, neo4j: Neo4jConnector, extractor: CategoryExtractor, embedder: Any):
        self._neo4j = neo4j
        self._extractor = extractor
        self._embedder = embedder

    @staticmethod
    def make_doc_key(path: str) -> str:
        abs_path = os.path.abspath(path)
        stat = os.stat(abs_path)
        raw = f"{abs_path}|{stat.st_mtime_ns}|{stat.st_size}"
        return hashlib.sha1(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _make_prefix(path: str, doc_key: str) -> str:
        base = os.path.splitext(os.path.basename(path))[0]
        safe = re.sub(r"[^0-9A-Za-z_]+", "_", base).strip("_") or "doc"
        return f"{safe[:24]}_{doc_key}"

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[가-힣A-Za-z0-9]{2,}", text.lower()))

    def _kw_overlap(self, chunk_text: str, leaf_text: str) -> float:
        c = self._tokenize(chunk_text)
        if not c:
            return 0.0
        t = self._tokenize(leaf_text)
        if not t:
            return 0.0
        return len(c & t) / max(1, len(c))

    def _select_leaf_category(
        self,
        chunk_text: str,
        chunk_emb: np.ndarray,
        leaf_nodes: list[CategoryNode],
        leaf_embs: np.ndarray,
        leaf_texts: list[str],
    ) -> tuple[CategoryNode, float]:
        sims = cosine_similarity([chunk_emb], leaf_embs)[0]
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])

        if best_sim >= SIM_THRESHOLD:
            cand_idx = list(np.argsort(sims)[-3:][::-1])
            sim_w, kw_w = 0.80, 0.20
        else:
            cand_idx = list(np.argsort(sims)[-6:][::-1])
            sim_w, kw_w = 0.55, 0.45

        chosen_idx = best_idx
        best_score = -1.0
        for idx in cand_idx:
            kw = self._kw_overlap(chunk_text, leaf_texts[idx])
            score = sim_w * float(sims[idx]) + kw_w * kw
            if score > best_score:
                best_score = score
                chosen_idx = int(idx)

        return leaf_nodes[chosen_idx], best_sim

    def run(self, pdf_path: str) -> bool:
        doc_key = self.make_doc_key(pdf_path)
        if self._neo4j.is_indexed(doc_key):
            print(f"  ⏭  이미 인덱싱됨, 스킵: {os.path.basename(pdf_path)}")
            return False

        prefix = self._make_prefix(pdf_path, doc_key)
        abs_pdf_path = os.path.abspath(pdf_path)

        self._neo4j.save_document(doc_key, abs_pdf_path)
        print(f"\n{'─'*55}")
        print(f"  📄 {os.path.basename(pdf_path)}  (key={doc_key})")
        print(f"{'─'*55}")

        print("  [1/4] PDF 파싱 & 청킹...")
        pages = PDFParser.extract_text(pdf_path)
        chunks = PDFParser.chunk_pages(pages)
        for c in chunks:
            c.chunk_id = f"{prefix}_{c.chunk_id}"
        print(f"        -> {len(chunks)}개 청크")

        print("  [2/4] 카테고리 구조 추출...")
        cat_json = self._extractor.extract(chunks, pages=pages)

        print("  [3/4] 카테고리 임베딩 계산 & Neo4j MERGE...")
        leaf_nodes: list[CategoryNode] = []

        for top_cat in cat_json.get("categories", []):
            top_id = f"{prefix}_{top_cat['id']}"
            parent = CategoryNode(
                node_id=top_id,
                name=top_cat["name"],
                level=0,
                keywords=top_cat.get("keywords", []),
            )
            parent.embedding = self._embedder.encode(parent.name + " " + " ".join(parent.keywords))
            self._neo4j.merge_category(parent, doc_key)
            self._neo4j.link_document_to_category(doc_key, top_id)

            for sub in top_cat.get("subcategories", []):
                sub_id = f"{prefix}_{sub['id']}"
                child = CategoryNode(
                    node_id=sub_id,
                    name=sub["name"],
                    level=1,
                    keywords=sub.get("keywords", []),
                )
                child.embedding = self._embedder.encode(child.name + " " + " ".join(child.keywords))
                self._neo4j.merge_category(child, doc_key)
                self._neo4j.merge_subcategory_edge(top_id, sub_id)
                leaf_nodes.append(child)

        if not leaf_nodes:
            print("  [경고] 하위 카테고리가 없어 청크를 저장하지 않습니다.")
            self._neo4j.save_document(doc_key, abs_pdf_path)
            return True

        print("  [4/4] 청크 임베딩 계산 & Neo4j MERGE...")
        leaf_embs = np.array([n.embedding for n in leaf_nodes])
        leaf_texts = [f"{n.name} {' '.join(n.keywords)}" for n in leaf_nodes]
        chunk_embs = self._embedder.encode([c.text for c in chunks], show_progress_bar=False)

        assigned = Counter()
        low_sim_count = 0

        for chunk, c_emb in zip(chunks, chunk_embs):
            chunk.embedding = c_emb
            best, top_sim = self._select_leaf_category(chunk.text, c_emb, leaf_nodes, leaf_embs, leaf_texts)
            if top_sim < SIM_THRESHOLD:
                low_sim_count += 1
            assigned[best.name] += 1
            self._neo4j.merge_chunk(chunk, best.node_id, doc_key)

        if assigned:
            top_dist = ", ".join(f"{k}:{v}" for k, v in assigned.most_common(5))
            print(f"        -> 상위 분포(top5): {top_dist}")
            if low_sim_count > 0:
                print(f"        -> 저유사도 보정 매핑: {low_sim_count}청크")

        self._neo4j.save_document(doc_key, abs_pdf_path)
        print(f"  ✅ 저장 완료  ({len(chunks)}청크 / {len(leaf_nodes)}하위카테고리)")
        return True
