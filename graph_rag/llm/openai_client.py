"""
graph_rag/llm/openai_client.py

역할:
- KB 구축 단계(초기 1회)에만 사용하는 OpenAI API 클라이언트.
- 엔티티·관계 추출: JSON Schema를 강제하여 스키마 밖 관계 생성을 방지한다.
- 흐름도 이미지 파싱: OpenAI Vision API를 통해 노드/엣지를 JSON으로 추출한다.

구현 원칙:
- LLM에 자유 텍스트 출력 허용 금지
- 반드시 JSON 형식의 구조화 출력만 허용
- 허용 predicate 7개 외 관계 생성 불가
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from graph_rag.config import ALLOWED_PREDICATES, OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

# LLM 추출용 JSON Schema (구조화 출력 강제)
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

_JSON_SCHEMA = {
    "name": "entity_relation_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "domain": {"type": "string"},
                        "summary": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["id", "name", "type", "domain", "summary", "confidence"],
                },
            },
            "relations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "subject_id": {"type": "string"},
                        "predicate": {"type": "string"},
                        "object_id": {"type": "string"},
                        "condition": {"type": "string"},
                        "confidence": {"type": "number"},
                        "source_text": {"type": "string"},
                    },
                    "required": ["subject_id", "predicate", "object_id", "condition", "confidence", "source_text"],
                },
            },
        },
        "required": ["entities", "relations"],
    },
}


class OpenAIKBClient:
    """KB 구축용 OpenAI API 클라이언트."""

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self._client = OpenAI(api_key=OPENAI_API_KEY)
        self._model = OPENAI_MODEL

    def extract_entities_and_relations(
        self, text: str, source_file: str = ""
    ) -> Dict[str, Any]:
        """
        텍스트에서 엔티티와 관계를 추출한다.
        Returns: {"entities": [...], "relations": [...]}
        """
        user_content = (
            f"[출처: {source_file}]\n\n"
            f"다음 텍스트에서 엔티티와 관계를 추출하세요:\n\n{text[:3000]}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_schema", "json_schema": _JSON_SCHEMA},
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)

        except json.JSONDecodeError as exc:
            logger.error("OpenAI 응답 JSON 파싱 실패: %s", exc)
            return {"entities": [], "relations": []}
        except Exception as exc:
            logger.error("OpenAI API 오류: %s", exc)
            return {"entities": [], "relations": []}

    def parse_flowchart_image(self, image_path: Path) -> Dict[str, Any]:
        """
        흐름도 이미지에서 노드와 엣지를 추출한다 (OpenAI Vision).
        Returns: {"entities": [...], "relations": [...]}
        """
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

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
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                },
                            },
                            {"type": "text", "text": flowchart_prompt},
                        ],
                    },
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_schema", "json_schema": _JSON_SCHEMA},
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)

        except Exception as exc:
            logger.error("흐름도 파싱 실패 (%s): %s", image_path, exc)
            return {"entities": [], "relations": []}
