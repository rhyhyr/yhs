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

_ANSWER_PROMPT_TEMPLATE = """당신은 동아대학교 외국인 유학생 지원 챗봇입니다.

[엄격한 규칙]
1. 아래 [참조 문서]에 명시된 내용만 근거로 답하세요.
2. 참조 문서에 정보가 없으면 정확히 다음과 같이만 답하세요:
   "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처(연락처)
    또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
3. 추측, 일반 상식, 외부 지식 사용 금지.
4. 한국어로만 답변. 다른 언어 단어 절대 금지 (예: 总之, まず, 申请 등).
5. 답변 끝에 사용한 출처를 [문서명, 페이지] 형식으로 반드시 명시.
6. 답변은 3~6문장 이내. 불필요한 정보 추가 금지.

[답변 정책]
참조 문서가 질문과 100% 일치하지 않더라도, 관련된 정보가 있다면
다음 형식으로 부분 답변을 제공하세요:

"[관련 정보 요약]. 다만 이는 [참조 문서명] 기준이며, 정확한
[질문 키워드]에 대해서는 동아대 국제교류처 또는
하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."

참조 문서가 질문과 전혀 무관할 때만 "제공된 자료에서는 확인할 수 없습니다"
응답을 사용하세요.

[참조 문서]
{retrieved_chunks}

[질문]
{user_question}
"""

_ANSWER_PROMPT_WEB_TEMPLATE = """당신은 동아대학교 외국인 유학생 지원 챗봇입니다.

[엄격한 규칙]
1. 아래 [참조 문서]에 명시된 내용만 근거로 답하세요.
2. 참조 문서에 정보가 없으면 정확히 다음과 같이만 답하세요:
   "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처(연락처)
    또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
3. 추측, 일반 상식, 외부 지식 사용 금지.
4. 한국어로만 답변. 다른 언어 단어 절대 금지 (예: 总之, まず, 申请 등).
5. 답변 끝에 사용한 출처 URL을 반드시 명시.
6. 답변은 3~6문장 이내. 불필요한 정보 추가 금지.

[답변 정책]
참조 문서가 질문과 100% 일치하지 않더라도, 관련된 정보가 있다면 해당 내용을 바탕으로 답변하세요.
참조 문서가 질문과 전혀 무관할 때만 "제공된 자료에서는 확인할 수 없습니다" 응답을 사용하세요.

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
            answer = self._call(prompt, max_tokens=2048)
            if not answer:
                return _STRICT_NO_ANSWER
            if _has_forbidden_script(answer):
                logger.warning("비한국어 스크립트 검출로 답변 폐기")
                return _STRICT_NO_ANSWER
            return answer
        except Exception as exc:
            logger.error("Gemini 답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER
