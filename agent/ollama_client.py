"""
agent/ollama_client.py

역할:
- 런타임 답변 생성 전용 EXAONE 3.5 7B 로컬 LLM 클라이언트 (Ollama).
- 질문 정규화 및 답변 생성.
"""

from __future__ import annotations

import logging

import requests

from graph_rag.config import NO_ANSWER_RESPONSE, OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """당신은 동아대학교 유학생 지원 AI 에이전트입니다.

반드시 다음 규칙을 지켜야 합니다:
1. 제공된 [그래프 트리플]과 [원문] 정보만 사용하여 답변하세요.
2. 제공된 정보에 없는 내용은 절대 만들어내지 마세요.
3. 정보가 부족하면 "해당 정보를 찾을 수 없습니다"라고 명확히 말하세요.
4. 답변 마지막에 반드시 출처(문서명, 버전)를 표기하세요.
5. 비자 정책은 변경될 수 있으므로 최신 정보는 공식 기관에서 확인하도록 안내하세요."""

_NORMALIZE_PROMPT = """다음 질문에서 언급된 비자/행정 개념을 표준 용어로 추출하세요.

규칙:
- 비표준 표현("비자 늘리기" → "비자 연장", "체류 기간 더 받기" → "체류기간 연장")을 표준화하세요.
- 비자 코드(D-2, D-4, F-5 등)는 그대로 유지하세요.
- 결과는 표준화된 키워드를 쉼표로 구분하여 반환하세요. 다른 텍스트는 포함하지 마세요.

질문: {question}"""


class OllamaRuntimeClient:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_url = f"{self._base_url}/api/generate"

    def _call(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }
        try:
            resp = requests.post(self._api_url, json=payload, timeout=OLLAMA_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            logger.error("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요: %s", self._base_url)
            raise
        except Exception as exc:
            logger.error("Ollama 호출 실패: %s", exc)
            raise

    def normalize_question(self, question: str) -> str:
        try:
            prompt = _NORMALIZE_PROMPT.format(question=question)
            return self._call(prompt, max_tokens=128)
        except Exception:
            return ""

    def generate_answer(self, question: str, context: str, result: RetrievalResult) -> str:
        if result.retrieval_method == "no_answer" or not context:
            return NO_ANSWER_RESPONSE

        user_prompt = f"[질문]\n{question}\n\n{context}"

        try:
            answer = self._call(user_prompt, system=_SYSTEM_PROMPT, max_tokens=1024)
            return answer if answer else NO_ANSWER_RESPONSE
        except Exception as exc:
            logger.error("답변 생성 실패: %s", exc)
            return NO_ANSWER_RESPONSE

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
