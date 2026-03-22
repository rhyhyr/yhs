"""카테고리 추출 모듈.

역할:
- Gemini로 상/하위 카테고리 JSON 생성
- 실패 시 헤더 기반/로컬 규칙 기반 폴백으로 계속 진행
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Optional

import numpy as np
from google.api_core import exceptions as gapi_exceptions

from .models import Chunk


class CategoryExtractor:
    """문서 청크를 받아 계층 카테고리 구조를 생성한다."""
    _PROMPT = """당신은 문서 분석 전문가입니다.
아래 문서 텍스트를 분석하여 계층적 카테고리 구조를 JSON으로만 반환하세요.

출력 형식 (순수 JSON만, 마크다운 코드블록 없이):
{{
  "categories": [
    {{
      "id": "cat_0",
      "name": "상위 카테고리명",
      "keywords": ["키워드1", "키워드2", "키워드3"],
      "subcategories": [
        {{
          "id": "cat_0_0",
          "name": "하위 카테고리명",
          "keywords": ["키워드1", "키워드2"]
        }}
      ]
    }}
  ]
}}

규칙:
- 상위 카테고리 3~6개, 각 상위에 하위 2~4개
- 키워드는 해당 카테고리를 대표하는 명사/동사구 (한국어)
- JSON 외 텍스트 출력 금지

[문서 텍스트]
{text}"""

    _STOPWORDS = {
        "그리고", "또는", "에서", "으로", "대한", "관련", "있습니다", "합니다",
        "the", "and", "for", "with", "that", "this", "from",
    }

    def __init__(self, model: Any):
        self._model = model

    def _heading_fallback(self, pages: list[tuple[int, str]]) -> Optional[dict]:
        chapter_pat = re.compile(r"^(제\d+장)\s+(.+)$")
        section_pat = re.compile(r"^(제\d+절)\s+(.+)$")

        tops: list[dict[str, Any]] = []
        current_top: Optional[dict[str, Any]] = None

        for _, page_text in pages:
            for line in page_text.splitlines():
                s = line.strip()
                m_ch = chapter_pat.match(s)
                if m_ch:
                    current_top = {"label": m_ch.group(1), "name": m_ch.group(2).strip(), "sub": []}
                    tops.append(current_top)
                    continue

                m_sec = section_pat.match(s)
                if m_sec and current_top is not None:
                    current_top["sub"].append({"label": m_sec.group(1), "name": m_sec.group(2).strip()})

        if not tops:
            return None

        categories: list[dict[str, Any]] = []
        for i, t in enumerate(tops):
            sub = t["sub"][:6] or [{"label": f"{t['label']}-1", "name": f"{t['name']} 일반"}]
            categories.append(
                {
                    "id": f"cat_{i}",
                    "name": t["name"],
                    "keywords": [t["label"], t["name"]],
                    "subcategories": [
                        {
                            "id": f"cat_{i}_{j}",
                            "name": s["name"],
                            "keywords": [s["label"], s["name"]],
                        }
                        for j, s in enumerate(sub)
                    ],
                }
            )

        return {"categories": categories}

    def _local_fallback(self, chunks: list[Chunk]) -> dict:
        if not chunks:
            return {"categories": []}

        top_k = max(3, min(6, len(chunks) // 50 + 2))
        bucket_size = max(1, int(np.ceil(len(chunks) / top_k)))
        categories = []

        for i in range(top_k):
            group = chunks[i * bucket_size : (i + 1) * bucket_size]
            if not group:
                continue

            tokens = [
                t
                for ch in group
                for t in re.findall(r"[가-힣A-Za-z]{2,}", ch.text)
                if t not in self._STOPWORDS
            ]
            top_words = [w for w, _ in Counter(tokens).most_common(6)] or ["내용", "규정", "절차"]
            kw1 = top_words[:3]
            kw2 = top_words[3:6] if len(top_words) >= 6 else top_words[:3]

            categories.append(
                {
                    "id": f"cat_{i}",
                    "name": f"문서영역_{i + 1}",
                    "keywords": kw1,
                    "subcategories": [
                        {"id": f"cat_{i}_0", "name": f"문서영역_{i + 1}_주요", "keywords": kw1},
                        {"id": f"cat_{i}_1", "name": f"문서영역_{i + 1}_세부", "keywords": kw2},
                    ],
                }
            )
        return {"categories": categories}

    def extract(
        self,
        chunks: list[Chunk],
        pages: Optional[list[tuple[int, str]]] = None,
        sample_ratio: float = 0.3,
    ) -> dict:
        step = max(1, int(1 / sample_ratio))
        sample = "\n\n".join(c.text for c in chunks[::step])[:8000]

        try:
            resp = self._model.generate_content(self._PROMPT.format(text=sample))
            raw = resp.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            result = json.loads(raw)
            print("  [카테고리] Gemini 추출 성공")
            return result

        except gapi_exceptions.ResourceExhausted as e:
            print(f"  [카테고리] Gemini 쿼터 초과(429) -> 로컬 폴백 사용\n             {type(e).__name__}: {e}")
        except json.JSONDecodeError as e:
            print(f"  [카테고리] Gemini 응답 JSON 파싱 실패 -> 로컬 폴백 사용\n             {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  [카테고리] Gemini 오류 -> 로컬 폴백 사용\n             {type(e).__name__}: {e}")

        if pages:
            heading_result = self._heading_fallback(pages)
            if heading_result and heading_result.get("categories"):
                print("  [카테고리] 헤더 기반 폴백 사용(장/절 감지)")
                return heading_result
        return self._local_fallback(chunks)
