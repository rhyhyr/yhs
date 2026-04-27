"""
agent/ollama_client.py

역할:
- 런타임 답변 생성 전용 EXAONE 3.5 7B 로컬 LLM 클라이언트 (Ollama).
- 질문 정규화 및 답변 생성.
"""

from __future__ import annotations

import logging

import requests

from graph_rag.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
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

[참조 문서]
{retrieved_chunks}

[질문]
{user_question}
"""

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
        self._session = requests.Session()

    def _call(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }
        try:
            resp = self._session.post(self._api_url, json=payload, timeout=OLLAMA_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            logger.error("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요: %s", self._base_url)
            raise
        except Exception as exc:
            logger.error("Ollama 호출 실패: %s", exc)
            raise

    def close(self) -> None:
        self._session.close()

    def normalize_question(self, question: str) -> str:
        try:
            prompt = _NORMALIZE_PROMPT.format(question=question)
            return self._call(prompt, max_tokens=128)
        except Exception:
            return ""

    def generate_answer(self, question: str, context: str, result: RetrievalResult) -> str:
        if result.retrieval_method == "no_answer" or not context:
            return _STRICT_NO_ANSWER

        user_prompt = _ANSWER_PROMPT_TEMPLATE.format(
            retrieved_chunks=context,
            user_question=question,
        )

        try:
            answer = self._call(user_prompt, system="", max_tokens=1024)
            return answer if answer else _STRICT_NO_ANSWER
        except Exception as exc:
            logger.error("답변 생성 실패: %s", exc)
            return _STRICT_NO_ANSWER

    def is_available(self) -> bool:
        try:
            resp = self._session.get(f"{self._base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
