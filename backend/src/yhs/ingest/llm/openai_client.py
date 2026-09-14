"""
yhs/ingest/llm/openai_client.py

역할:
- KB 구축(인제스트)용 OpenAI API 클라이언트.
- 엔티티·관계 추출: JSON Schema 를 strict 로 강제한다.

왜 KB 구축에 OpenAI 를 쓰는가:
    로컬 Qwen 은 구조화 출력을 강제할 수단이 없다. 프롬프트로 "relations 의
    subject/object 는 entities 의 name 과 같아야 한다"고 아무리 써도 모델이
    지키지 않으면 그대로 통과하고, 검증 단계에서 대량으로 버려진다. 실제
    12청크 검증에서 관계 130건 중 8건(6%)만 살아남았다 — endpoint 누락
    81건, 타입 불일치 41건.

    OpenAI 는 strict json_schema 로 디코딩 단계에서 스키마를 강제한다.
    entity type, predicate, chunk_type 이 enum 으로 고정되고 필수 필드가
    보장되므로, 검증 단계에서 버릴 것이 크게 줄어든다.

주의:
    프롬프트는 provider 공용이다 (prompts.EXTRACTION_SYSTEM_PROMPT).
    여기서 따로 만들지 말 것. 예전에 그렇게 해서 이 파일만 옛 스키마
    (모델이 id 를 생성, type 4종, evidence 없음)에 멈춰 있었고, provider 를
    바꾸는 순간 검증이 전부 걸러내는 상태였다.
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from yhs.core.config import OPENAI_API_KEY, OPENAI_MODEL
from yhs.ingest.llm.prompts import EXTRACTION_SYSTEM_PROMPT
from yhs.ingest.validation import CHUNK_TYPES, ENTITY_TYPES, PREDICATE_TYPES

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = EXTRACTION_SYSTEM_PROMPT

# strict json_schema 는 additionalProperties:false 와 모든 속성의 required
# 명시를 요구한다.
#
# enum 은 validation.py 를 그대로 따라간다. 프롬프트 표와 검증 표가 어긋나면
# 모델이 규칙을 지켜도 코드가 버리게 되므로, 양쪽 모두 validation.py 한 곳만
# 본다.
_JSON_SCHEMA = {
    "name": "entity_relation_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["chunk_type", "entities", "relations"],
        "properties": {
            "chunk_type": {
                "type": "string",
                "enum": sorted(CHUNK_TYPES),
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    # id 는 받지 않는다. 코드가 name 에서 canonical id 를 만든다
                    # (ingestor._canonical_id). 모델이 id 를 지어내면 같은
                    # 개념이 D-1 / Foreign_student 처럼 갈라진다.
                    "required": ["name", "type", "summary", "confidence"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": sorted(ENTITY_TYPES)},
                        "summary": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                },
            },
            "relations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["subject", "predicate", "object",
                                 "condition", "evidence", "confidence"],
                    "properties": {
                        "subject": {"type": "string"},
                        "predicate": {
                            "type": "string",
                            "enum": sorted(PREDICATE_TYPES),
                        },
                        "object": {"type": "string"},
                        "condition": {"type": "string"},
                        # 근거를 못 대는 관계는 validation 에서 버려진다.
                        "evidence": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                },
            },
        },
    },
}

_EMPTY: dict[str, Any] = {"chunk_type": "", "entities": [], "relations": []}


class OpenAIKBClient:
    """KB 구축용 OpenAI API 클라이언트."""

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self._client = OpenAI(api_key=OPENAI_API_KEY)
        self._model = OPENAI_MODEL

    def _complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """strict json_schema 로 한 번 호출하고 파싱한다.

        gpt-5 계열은 max_tokens 를 받지 않고 max_completion_tokens 를 쓴다.
        추론 토큰이 이 한도를 같이 먹으므로 넉넉히 준다 — 한도에 걸리면
        content 가 빈 문자열로 돌아오고, 그러면 그 청크가 통째로 사라진다.
        """
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_completion_tokens=8000,
            response_format={"type": "json_schema", "json_schema": _JSON_SCHEMA},
        )
        choice = response.choices[0]
        raw = choice.message.content or ""

        if not raw.strip():
            # 토큰 한도에 걸려 잘렸거나 안전 필터에 막힌 경우.
            # 빈 결과를 조용히 돌려주면 "그래프가 빈약하다"로만 보인다.
            logger.error(
                "OpenAI 응답이 비어 있음 (finish_reason=%s, usage=%s)",
                choice.finish_reason, response.usage,
            )
            raise ValueError(f"빈 응답 (finish_reason={choice.finish_reason})")

        return json.loads(raw)

    def extract_entities_and_relations(
        self, text: str, source_file: str = ""
    ) -> dict[str, Any]:
        """텍스트에서 chunk_type·엔티티·관계를 추출한다.

        Returns: {"chunk_type": str, "entities": [...], "relations": [...]}
        """
        user_content = (
            f"[출처: {source_file}]\n\n"
            f"다음 문단을 3단계 절차대로 처리하세요:\n\n{text[:3000]}"
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            return self._complete(messages)
        except json.JSONDecodeError as exc:
            # strict 스키마에서는 거의 일어나지 않는다. 일어나면 알아야 한다.
            logger.error("OpenAI 응답 JSON 파싱 실패: %s", exc)
            raise
        except Exception as exc:
            # 여기서 삼키면 LLMExtractor 의 STATS 집계를 지나쳐 버린다.
            # 실패는 위로 올려 집계에 남긴다.
            logger.error("OpenAI API 오류: %s", exc)
            raise

    def parse_flowchart_image(self, image_path: Path) -> dict[str, Any]:
        """흐름도 이미지에서 노드와 엣지를 추출한다 (OpenAI Vision).

        현재 파이프라인에서 호출되는 곳은 없다. 추출 스키마를 바꿀 때 같이
        갱신해 두어야 나중에 되살릴 때 어긋나지 않는다.
        """
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        media_type = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        }.get(image_path.suffix.lower(), "image/png")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
                    {"type": "text",
                     "text": "이 흐름도의 노드와 화살표를 위 3단계 절차대로 "
                             "추출하세요. 화살표의 조건문은 condition 에 넣으세요."},
                ],
            },
        ]

        try:
            return self._complete(messages)
        except Exception as exc:
            logger.error("흐름도 파싱 실패 (%s): %s", image_path, exc)
            return dict(_EMPTY)
