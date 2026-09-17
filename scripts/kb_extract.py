"""
scripts/kb_extract.py

147청크를 LLM 으로 추출해 JSONL 로 저장한다. Neo4j 에는 쓰지 않는다.

왜 분리하나:
    추출과 적재가 한 덩어리였을 때는 검증 규칙 한 줄을 바꿔도 147번의 API
    호출을 다시 해야 했다. 그래서 매번 "돌려보고 나서야" 문제를 알았고,
    12청크 샘플로 통과 판정을 내렸다가 전수에서 listing 오분류 103건이
    드러나는 일이 생겼다.

    추출 결과를 파일로 남겨 두면 검증·정규화 규칙은 API 재호출 없이 몇
    번이든 다시 적용할 수 있다 (scripts/kb_analyze.py).

캐시:
    (chunk_id, model, prompt_version, schema_hash) 가 모두 같으면 다시
    부르지 않는다. 프롬프트를 고쳐 PROMPT_VERSION 을 올리면 그 청크만
    다시 호출된다. --only 로 특정 청크만 강제 재추출할 수도 있다.

실행:
    docker compose exec -T -e LLM_PROVIDER=openai -e PYTHONIOENCODING=utf-8 \
        backend python - < scripts/kb_extract.py

    환경변수
      OUT        출력 JSONL 경로 (기본 /data/extract/raw.jsonl)
      ONLY       쉼표로 구분한 chunk_id — 이것만 재추출 (캐시 무시)
      REFRESH    yes 면 캐시를 통째로 무시하고 전부 다시 호출
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from yhs.core.config import PDF_DIR
from yhs.ingest.llm.prompts import PROMPT_VERSION
from yhs.ingest.pipeline.chunker import chunk_documents
from yhs.ingest.pipeline.cleaner import clean_text
from yhs.ingest.pipeline.extractor import LLMExtractor
from yhs.ingest.pipeline.loader import PDFLoader

OUT = Path(os.getenv("OUT", "/data/extract/raw.jsonl"))
ONLY = {c.strip() for c in os.getenv("ONLY", "").split(",") if c.strip()}
REFRESH = os.getenv("REFRESH", "").lower() in {"1", "yes", "true"}


def _schema_hash() -> str:
    """출력 스키마가 바뀌면 캐시를 무효화하기 위한 지문."""
    try:
        from yhs.ingest.llm.openai_client import _JSON_SCHEMA
        blob = json.dumps(_JSON_SCHEMA, sort_keys=True, ensure_ascii=False)
    except Exception:
        blob = "(provider 에 json schema 없음)"
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def _load_cache(path: Path) -> dict[str, dict]:
    """기존 JSONL 을 chunk_id 로 읽어들인다. 깨진 줄은 버린다."""
    cache: dict[str, dict] = {}
    if not path.is_file():
        return cache
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("chunk_id"):
                cache[rec["chunk_id"]] = rec
    return cache


def main() -> int:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    extractor = LLMExtractor()
    client = extractor._get_client()
    model = getattr(client, "_model", None) or getattr(client, "_model_name", provider)
    schema_hash = _schema_hash()

    print(f"provider={provider}  model={model}  "
          f"prompt_version={PROMPT_VERSION}  schema={schema_hash}")

    # ── 청킹 (LLM 없이) ─────────────────────────────────────────────────
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"PDF 가 없습니다: {PDF_DIR}", file=sys.stderr)
        return 1

    loader = PDFLoader()
    chunks = []
    for pdf in pdf_files:
        docs = loader.load(pdf)
        for d in docs:
            d.text = clean_text(d.text)
        chunks.extend(chunk_documents(docs))
    print(f"문서 {len(pdf_files)}개 → 청크 {len(chunks)}개\n")

    # ── 캐시 확인 ───────────────────────────────────────────────────────
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cache = {} if REFRESH else _load_cache(OUT)

    def is_fresh(c) -> bool:
        rec = cache.get(c.id)
        if rec is None:
            return False
        if ONLY and c.id in ONLY:
            return False
        return (
            rec.get("model") == model
            and rec.get("prompt_version") == PROMPT_VERSION
            and rec.get("schema_hash") == schema_hash
            and rec.get("error") is None
        )

    todo = [c for c in chunks if not is_fresh(c)]
    print(f"캐시 재사용 {len(chunks) - len(todo)}청크 / 새로 호출 {len(todo)}청크\n")

    # ── 추출 ────────────────────────────────────────────────────────────
    started = time.time()
    for i, c in enumerate(todo, 1):
        rec = {
            "chunk_id": c.id,
            "source_file": c.source_file,
            "source_page": c.source_page,
            "section": c.section,
            "chunk_text": c.text,
            "chunk_sha1": hashlib.sha1(c.text.encode("utf-8")).hexdigest(),
            "model": model,
            "provider": provider,
            "prompt_version": PROMPT_VERSION,
            "schema_hash": schema_hash,
            "extracted_at": datetime.now().isoformat(timespec="seconds"),
            "error": None,
            "raw_response": None,
        }
        try:
            rec["raw_response"] = client.extract_entities_and_relations(
                c.text, c.source_file
            )
        except Exception as exc:
            # 실패도 기록한다. 조용히 빠지면 나중에 청크 수가 안 맞는 이유를
            # 알 수 없다. error 가 있는 레코드는 다음 실행에서 다시 호출된다.
            rec["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  [{i}/{len(todo)}] 실패 {c.id[:12]} {c.source_file[:30]} "
                  f"— {rec['error'][:80]}")
        else:
            raw = rec["raw_response"]
            print(f"  [{i}/{len(todo)}] {c.id[:12]} {c.source_file[:34]:36} "
                  f"{raw.get('chunk_type', '?'):12} "
                  f"E{len(raw.get('entities', []))} R{len(raw.get('relations', []))}")
        cache[c.id] = rec

    # ── 저장 (청크 순서대로 다시 쓴다) ──────────────────────────────────
    order = [c.id for c in chunks]
    with OUT.open("w", encoding="utf-8") as f:
        for cid in order:
            rec = cache.get(cid)
            if rec is not None:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    failed = sum(1 for cid in order if (cache.get(cid) or {}).get("error"))
    elapsed = time.time() - started
    print(f"\n저장: {OUT}  ({len(order)}줄, 실패 {failed}건, {elapsed / 60:.1f}분)")
    if failed:
        print("  실패한 청크는 다시 실행하면 그것만 재호출됩니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
