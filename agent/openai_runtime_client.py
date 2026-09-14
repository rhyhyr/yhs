"""
agent/openai_runtime_client.py

역할:
- OpenAI API를 통한 런타임 답변 생성 클라이언트.
- OllamaRuntimeClient와 동일한 인터페이스 → 드롭인 교체 가능.

사용:
    .env에 OPENAI_API_KEY 설정
    OPENAI_RUNTIME_MODEL=gpt-4o-mini (기본값)
"""

from __future__ import annotations

import logging
import os

from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt-4o-mini"

_STRICT_NO_ANSWER = (
    "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 "
    "또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
)

_SYSTEM_PROMPT = """당신은 동아대학교 외국인 유학생을 돕는 친절한 AI 어시스턴트입니다.

[규칙]
1. 아래 [참조 문서]에 있는 내용을 최대한 활용해서 구체적으로 답하세요.
2. 숫자·날짜·기간·전화번호·퍼센트는 [참조 문서]에 그대로 적힌 값만 사용하세요.
   문서에 없는 수치를 본인이 알고 있더라도 절대 쓰지 마세요.
3. 참조 문서에 관련 정보가 있다면, 그 정보를 바탕으로 충분히 설명하세요. "직접 문의하세요"로만 끝내지 마세요.
4. 참조 문서에 일부만 있으면: 알 수 있는 내용은 최대한 답하고, 부족한 부분만 "국제교류처에 문의"라고 덧붙이세요.
5. 참조 문서에 전혀 없으면: "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 또는 하이코리아(hikorea.go.kr)에 문의 바랍니다."
6. 추측 표현("일반적으로", "보통", "아마도")을 사용하지 마세요.
7. 한국어로만 답변하세요.
8. 답변 마지막에 출처를 [문서명, 페이지] 형식으로 표시하세요."""

_ANSWER_TEMPLATE = """[참조 문서]
{retrieved_chunks}

[질문]
{user_question}"""


class OpenAIRuntimeClient:
    """OpenAI API 기반 런타임 답변 생성 클라이언트."""

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self._client = OpenAI(api_key=api_key)
        self._model = model or os.environ.get("OPENAI_RUNTIME_MODEL", _DEFAULT_MODEL)
        logger.info("OpenAIRuntimeClient 초기화: %s", self._model)

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def close(self) -> None:
        pass

    def normalize_question(self, question: str) -> str:
        return ""

    def generate_answer(
        self,
        question: str,
        context: str,
        result: RetrievalResult,
        web_context: bool = False,
    ) -> str:
        if not context:
            return _STRICT_NO_ANSWER
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _ANSWER_TEMPLATE.format(
                        retrieved_chunks=context,
                        user_question=question,
                    )},
                ],
                temperature=0.0,
                max_tokens=1024,
            )
            answer = (resp.choices[0].message.content or "").strip()
            return answer if answer else _STRICT_NO_ANSWER
        except Exception as exc:
            logger.error("OpenAI 답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER
