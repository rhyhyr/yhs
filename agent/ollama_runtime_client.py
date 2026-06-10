"""
agent/ollama_runtime_client.py

역할:
- Ollama 로컬 서버를 통한 런타임 답변 생성 클라이언트.
- GeminiRuntimeClient와 동일한 인터페이스 → query_runner/api.py에서 드롭인 교체 가능.

사용:
    .env 또는 환경변수에 RUNTIME_LLM=ollama 설정
    OLLAMA_MODEL=exaone3.5:7b  (기본값)

전제:
    Ollama 서버 실행 중이어야 함 (ollama serve)
    모델이 설치되어 있어야 함 (ollama pull exaone3.5:7b)
"""

from __future__ import annotations

import logging

import requests

from graph_rag.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

_STRICT_NO_ANSWER = (
    "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 "
    "또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
)

_SYSTEM_PROMPT = """당신은 동아대학교 외국인 유학생을 돕는 친절한 AI 어시스턴트입니다.

[규칙]
1. 아래 [참조 문서]에 있는 내용을 최대한 활용해서 구체적으로 답하세요.
2. 참조 문서에 관련 정보가 있다면, 그 정보를 바탕으로 충분히 설명하세요. "직접 문의하세요"로 끝내지 마세요.
3. 참조 문서에 전혀 없는 내용은 추측하지 마세요.
4. 한국어로만 답변하세요.
5. 답변 마지막에 출처를 [문서명, 페이지] 형식으로 표시하세요."""

_ANSWER_TEMPLATE = """[참조 문서]
{retrieved_chunks}

[질문]
{user_question}"""

_NORMALIZE_SYSTEM = """다음 질문에서 비자/행정 개념을 표준 용어로 추출하세요.
비표준 표현("비자 늘리기" → "비자 연장")을 표준화하고, 비자 코드(D-2, D-4)는 그대로 유지하세요.
표준화된 키워드를 쉼표로 구분해서만 반환하세요."""


class OllamaRuntimeClient:
    """Ollama 로컬 서버 기반 런타임 답변 생성 클라이언트."""

    def __init__(self) -> None:
        self._base_url = OLLAMA_BASE_URL.rstrip("/")
        self._model = OLLAMA_MODEL
        self._chat_url = f"{self._base_url}/api/chat"
        self._tags_url = f"{self._base_url}/api/tags"
        self._session = requests.Session()
        logger.info("OllamaRuntimeClient 초기화: %s / %s", self._base_url, self._model)

    def is_available(self) -> bool:
        """Ollama 서버가 실행 중인지 확인."""
        try:
            resp = self._session.get(self._tags_url, timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        self._session.close()

    def _chat(self, system: str, user: str, max_tokens: int = 2048) -> str:
        """Ollama /api/chat 엔드포인트 호출."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = self._session.post(self._chat_url, json=payload, timeout=OLLAMA_TIMEOUT)
            resp.raise_for_status()
            return (resp.json().get("message", {}).get("content") or "").strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Ollama 서버에 연결할 수 없습니다. 'ollama serve' 실행 여부 확인: {self._base_url}"
            )
        except Exception as exc:
            logger.error("Ollama 호출 실패: %s", exc)
            raise

    def normalize_question(self, question: str) -> str:
        try:
            return self._chat(_NORMALIZE_SYSTEM, question, max_tokens=128) or ""
        except Exception as exc:
            logger.warning("Ollama 정규화 실패: %s", exc)
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

        user_text = _ANSWER_TEMPLATE.format(
            retrieved_chunks=context,
            user_question=question,
        )
        try:
            answer = self._chat(_SYSTEM_PROMPT, user_text, max_tokens=2048)
            return answer if answer else _STRICT_NO_ANSWER
        except ConnectionError as exc:
            logger.error("%s", exc)
            return _STRICT_NO_ANSWER
        except Exception as exc:
            logger.error("Ollama 답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER
