"""
graph_rag/llm/gemini_client.py

역할:
- KB 구축 단계(초기 1회)에만 사용하는 Gemini API 클라이언트.
- 엔티티·관계 추출: JSON 형식을 강제하여 스키마 밖 관계 생성을 방지한다.
- 흐름도 이미지 파싱: Gemini Vision API를 통해 노드/엣지를 JSON으로 추출한다.

구현 원칙:
- LLM에 자유 텍스트 출력 허용 금지
- 반드시 JSON 형식의 구조화 출력만 허용
- 허용 predicate 외 관계 생성 불가
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

from google import genai
from google.genai import types

from graph_rag.config import ALLOWED_PREDICATES, GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

_MAX_RETRIES = 4
_RETRY_BASE_WAIT = 15

_EXTRACTION_SCHEMA = {
    "entities": [
        {
            "id": "string (고유 식별자, 예: D-4)",
            "name": "string (표준 명칭)",
            "type": "string (Entity|Procedure|Document|Institution 중 하나)",
            "domain": "string (visa|health_insurance|part_time|school_admin|daily_life 중 하나)",
            "summary": "string (1-2문장 요약)",
            "confidence": "float [0.7-1.0]",
        }
    ],
    "relations": [
        {
            "subject_id": "string",
            "predicate": f"string ({' | '.join(ALLOWED_PREDICATES)} 중 하나만 허용)",
            "object_id": "string",
            "condition": "string (조건문이 있으면 여기에 기술, 없으면 빈 문자열)",
            "confidence": "float [0.7-1.0]",
            "source_text": "string (근거 원문 발췌, 50자 이내)",
        }
    ],
}

_SYSTEM_PROMPT = f"""당신은 행정 문서에서 엔티티와 관계를 추출하는 전문가입니다.

다음 규칙을 반드시 지켜야 합니다:
1. 출력은 반드시 아래 JSON 스키마 형식으로만 해야 합니다.
2. predicate는 반드시 허용 목록({', '.join(ALLOWED_PREDICATES)}) 중 하나여야 합니다.
3. 조건문("~인 경우", "~이상인 경우")은 별도 노드가 아닌 엣지의 condition 필드에 저장합니다.
4. confidence는 추출 확실성을 [0.7, 1.0] 범위로 표현합니다.
5. 확실하지 않으면 해당 항목을 포함하지 마세요.

출력 JSON 스키마:
{json.dumps(_EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)}

JSON 이외의 텍스트는 절대 출력하지 마세요."""


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "resource exhausted" in msg or "quota" in msg


def _call_with_retry(fn, *args, **kwargs) -> Any:
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if _is_rate_limit_error(exc) and attempt < _MAX_RETRIES:
                wait = _RETRY_BASE_WAIT * (2 ** attempt)
                logger.warning("Rate limit 초과. %d초 후 재시도 (%d/%d)...", wait, attempt + 1, _MAX_RETRIES)
                time.sleep(wait)
            else:
                raise


class GeminiKBClient:
    """KB 구축용 Gemini API 클라이언트."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._model = GEMINI_MODEL
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

    def extract_entities_and_relations(self, text: str, source_file: str = "") -> Dict[str, Any]:
        user_content = (
            f"[출처: {source_file}]\n\n"
            f"다음 텍스트에서 엔티티와 관계를 추출하세요:\n\n{text[:1500]}"
        )

        try:
            response = _call_with_retry(
                self._client.models.generate_content,
                model=self._model,
                contents=user_content,
                config=self._config,
            )
            raw = (response.text or "").strip()

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

            try:
                from json_repair import repair_json
                repaired = repair_json(raw)
                result = json.loads(repaired)
                logger.warning("JSON 복구 성공 (응답이 잘렸을 가능성 있음)")
                return result
            except Exception:
                pass

            logger.error("JSON 파싱 및 복구 모두 실패 — 해당 청크 건너뜀")
            return {"entities": [], "relations": []}

        except Exception as exc:
            logger.error("Gemini API 오류: %s", exc)
            return {"entities": [], "relations": []}

    def parse_flowchart_image(self, image_path: Path) -> Dict[str, Any]:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        suffix = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/png")

        flowchart_prompt = (
            "이 흐름도에서 노드(개념/상태)와 화살표(관계)를 추출하세요.\n"
            "각 화살표의 조건문(있으면)도 condition 필드에 포함하세요.\n\n"
            f"출력 JSON 스키마:\n{json.dumps(_EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)}\n\n"
            "JSON 이외의 텍스트는 절대 출력하지 마세요."
        )

        try:
            response = _call_with_retry(
                self._client.models.generate_content,
                model=self._model,
                contents=[
                    flowchart_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                ],
                config=self._config,
            )
            raw = (response.text or "").strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                from json_repair import repair_json
                return json.loads(repair_json(raw))

        except Exception as exc:
            logger.error("흐름도 파싱 실패 (%s): %s", image_path, exc)
            return {"entities": [], "relations": []}
