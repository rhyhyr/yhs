"""
agent/gemini_runtime_client.py

역할:
- 런타임 답변 생성용 Gemini 클라이언트.
- 질문 정규화 및 최종 답변 생성을 담당한다.
"""

from __future__ import annotations

import logging
import re

import google.generativeai as genai

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
    # CJK 통합한자, 히라가나, 가타카나, 태국어
    forbidden = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]")
    return bool(forbidden.search(text))


class GeminiRuntimeClient:
    def __init__(self, model: str = GEMINI_MODEL) -> None:
        self._model_name = model
        self._model = None
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self._model = self._init_model_with_fallback(self._model_name)

    def _init_model_with_fallback(self, preferred_model: str):
        """설정 모델이 지원되지 않으면 사용 가능한 Gemini 모델로 폴백한다."""
        candidates = [
            preferred_model,
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash-8b",
        ]

        # API에서 실제 사용 가능한 모델명을 수집해 후보 뒤에 추가한다.
        try:
            discovered: list[str] = []
            for m in genai.list_models():
                name = getattr(m, "name", "") or ""
                methods = list(getattr(m, "supported_generation_methods", []) or [])
                if not name or "generateContent" not in methods:
                    continue
                short_name = name.split("models/")[-1]
                if short_name and short_name not in discovered:
                    discovered.append(short_name)

            for name in discovered:
                if name not in candidates:
                    candidates.append(name)
        except Exception as exc:
            logger.warning("Gemini 모델 목록 조회 실패: %s", exc)

        for name in candidates:
            try:
                model = genai.GenerativeModel(model_name=name)
                # 짧은 호출로 지원 여부 확인
                model.generate_content(
                    "ping",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0,
                        max_output_tokens=8,
                    ),
                )
                if name != preferred_model:
                    logger.warning(
                        "요청 모델(%s) 대신 사용 가능한 모델(%s)로 폴백합니다.",
                        preferred_model,
                        name,
                    )
                self._model_name = name
                return model
            except Exception:
                continue

        logger.error("사용 가능한 Gemini 모델을 찾지 못했습니다.")
        return None

    def close(self) -> None:
        return None

    def is_available(self) -> bool:
        return self._model is not None

    def _call(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        top_p: float = 0.9,
    ) -> str:
        if self._model is None:
            raise RuntimeError("Gemini model is not configured")

        resp = self._model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
            ),
        )

        # 1) quick accessor 우선
        text = ""
        try:
            text = (resp.text or "").strip()
        except Exception:
            text = ""

        # 2) quick accessor 실패 시 후보 파트에서 직접 조합
        if not text:
            candidates = getattr(resp, "candidates", None) or []
            for cand in candidates:
                content = getattr(cand, "content", None)
                parts = getattr(content, "parts", None) or []
                merged = "".join(
                    (getattr(p, "text", "") or "")
                    for p in parts
                ).strip()
                if merged:
                    text = merged
                    break

        return text

    def normalize_question(self, question: str) -> str:
        try:
            prompt = _NORMALIZE_PROMPT.format(question=question)
            normalized = self._call(
                prompt,
                max_tokens=128,
                temperature=0.0,
                top_p=0.9,
            )
            return normalized if normalized else ""
        except Exception as exc:
            logger.warning("Gemini 정규화 실패: %s", exc)
            return ""

    def generate_answer(self, question: str, context: str, result: RetrievalResult) -> str:
        if result.retrieval_method == "no_answer" or not context:
            return _STRICT_NO_ANSWER

        prompt = _ANSWER_PROMPT_TEMPLATE.format(
            retrieved_chunks=context,
            user_question=question,
        )

        try:
            answer = self._call(
                prompt,
                max_tokens=2048,
                temperature=0.0,
                top_p=0.9,
            )
            if not answer:
                return _STRICT_NO_ANSWER
            if _has_forbidden_script(answer):
                logger.warning("비한국어 스크립트 검출로 답변 폐기")
                return _STRICT_NO_ANSWER
            return answer
        except Exception as exc:
            logger.error("Gemini 답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER
