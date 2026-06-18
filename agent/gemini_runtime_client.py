"""
agent/gemini_runtime_client.py

역할:
- 런타임 답변 생성용 Gemini 클라이언트.
- 질문 정규화 및 최종 답변 생성을 담당한다.
"""

from __future__ import annotations

import logging
import re

from google import genai
from google.genai import types

from graph_rag.config import GEMINI_API_KEY, GEMINI_MODEL
from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

_STRICT_NO_ANSWER = (
    "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처(연락처) "
    "또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
)

_ANSWER_PROMPT_TEMPLATE = """당신은 동아대학교 외국인 유학생을 돕는 친절한 AI 어시스턴트입니다.

[규칙]
1. 아래 [참조 문서]에 있는 내용을 최대한 활용해서 구체적으로 답하세요.
2. 참조 문서에 관련 정보가 있다면, 그 정보를 바탕으로 충분히 설명하세요. "직접 문의하세요"로 끝내지 마세요.
3. 참조 문서에 전혀 없는 내용은 추측하지 마세요.
4. 한국어로만 답변하세요.
5. 답변 마지막에 출처를 [문서명, 페이지] 형식으로 표시하세요.

[답변 방식]
- 참조 문서에 답이 있으면: 핵심 내용을 명확하게 설명하고, 절차·조건·주의사항이 있으면 모두 포함하세요.
- 참조 문서에 일부만 있으면: 알 수 있는 내용은 최대한 답하고, 부족한 부분만 "추가 확인이 필요하면 국제교류처에 문의"라고 덧붙이세요.
- 참조 문서에 전혀 없으면: "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 또는 하이코리아(hikorea.go.kr)에 문의 바랍니다."

[참조 문서]
{retrieved_chunks}

[질문]
{user_question}
"""

_ANSWER_PROMPT_WEB_TEMPLATE = """당신은 동아대학교 외국인 유학생을 돕는 친절한 AI 어시스턴트입니다.

[규칙]
1. 아래 [참조 문서](PDF 자료 + 웹 검색 결과 포함)를 최대한 활용해 구체적으로 답하세요.
2. 관련 정보가 있다면 충분히 설명하세요. "직접 문의하세요"로만 끝내지 마세요.
3. 참조 문서에 없는 내용은 추측하지 마세요.
4. 한국어로만 답변하세요.
5. 답변 마지막에 출처 URL, [문서명, 페이지]를 표시하세요.

[참조 문서]
{retrieved_chunks}

[질문]
{user_question}
"""

_NORMALIZE_PROMPT = """다음 질문에서 언급된 비자/행정 개념을 표준 용어로 추출하세요.

규칙:
- 비표준 표현("비자 늘리기" -> "비자 연장", "체류 기간 더 받기" -> "체류기간 연장")을 표준화하세요.
- 비자 코드(D-2, D-4, F-5 등)는 그대로 유지하세요.
- 결과는 표준화된 키워드를 쉼표로 구분하여 반환하세요. 다른 텍스트는 포함하지 마세요.

질문: {question}
"""


def _has_forbidden_script(text: str) -> bool:
    """한글/숫자/기본 문장부호 외 CJK/태국어 등 비허용 스크립트 검출."""
    if not text:
        return False
    forbidden = re.compile(r"[一-鿿぀-ヿ฀-๿]")
    return bool(forbidden.search(text))


class GeminiRuntimeClient:
    def __init__(self, model: str = GEMINI_MODEL) -> None:
        self._model_name = model
        self._client = None
        if GEMINI_API_KEY:
            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._model_name = self._resolve_model(model)

    def _resolve_model(self, preferred: str) -> str:
        """설정 모델이 지원되지 않으면 사용 가능한 Gemini 모델로 폴백한다."""
        candidates = [preferred, "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b"]

        try:
            for m in self._client.models.list():
                name = getattr(m, "name", "") or ""
                short = name.split("models/")[-1]
                if short and short not in candidates:
                    candidates.append(short)
        except Exception as exc:
            logger.warning("Gemini 모델 목록 조회 실패: %s", exc)

        for name in candidates:
            try:
                self._client.models.generate_content(
                    model=name,
                    contents="ping",
                    config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
                )
                if name != preferred:
                    logger.warning("요청 모델(%s) 대신 %s로 폴백합니다.", preferred, name)
                return name
            except Exception:
                continue

        logger.error("사용 가능한 Gemini 모델을 찾지 못했습니다.")
        return preferred

    def close(self) -> None:
        return None

    def is_available(self) -> bool:
        return self._client is not None

    def _call(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.0, top_p: float = 0.9) -> str:
        if self._client is None:
            raise RuntimeError("Gemini client is not configured")

        resp = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
            ),
        )

        text = ""
        try:
            text = (resp.text or "").strip()
        except Exception:
            text = ""

        if not text:
            candidates = getattr(resp, "candidates", None) or []
            for cand in candidates:
                content = getattr(cand, "content", None)
                parts = getattr(content, "parts", None) or []
                merged = "".join((getattr(p, "text", "") or "") for p in parts).strip()
                if merged:
                    text = merged
                    break

        return text

    def normalize_question(self, question: str) -> str:
        try:
            return self._call(_NORMALIZE_PROMPT.format(question=question), max_tokens=128) or ""
        except Exception as exc:
            logger.warning("Gemini 정규화 실패: %s", exc)
            return ""

    def generate_answer(self, question: str, context: str, result: RetrievalResult, web_context: bool = False) -> str:
        if not context:
            return _STRICT_NO_ANSWER

        template = _ANSWER_PROMPT_WEB_TEMPLATE if web_context else _ANSWER_PROMPT_TEMPLATE
        prompt = template.format(retrieved_chunks=context, user_question=question)

        try:
            answer = self._call(prompt, max_tokens=4096)
            if not answer:
                return _STRICT_NO_ANSWER
            if _has_forbidden_script(answer):
                logger.warning("비한국어 스크립트 검출로 답변 폐기")
                return _STRICT_NO_ANSWER
            return answer
        except Exception as exc:
            logger.error("Gemini 답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER
