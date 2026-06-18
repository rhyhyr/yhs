"""
agent/hf_runtime_client.py

역할:
- HuggingFace 로컬 모델 기반 런타임 답변 생성 클라이언트.
- GeminiRuntimeClient와 동일한 인터페이스 → query_runner에서 드롭인 교체 가능.

사용:
    .env 또는 환경변수에 RUNTIME_LLM=hf 설정
    HF_RUNTIME_MODEL=Qwen/Qwen2.5-3B-Instruct  (기본값)
"""

from __future__ import annotations

import logging
import os

from graph_rag.schema.types import RetrievalResult

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "Qwen/Qwen2.5-3B-Instruct"

_STRICT_NO_ANSWER = (
    "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 "
    "또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다."
)

_SYSTEM_PROMPT = """당신은 동아대학교 외국인 유학생 지원 챗봇입니다.

규칙:
1. 아래 [참조 문서]에 있는 내용만 근거로 답하세요.
2. 참조 문서에 정보가 없으면: "제공된 자료에서는 확인할 수 없습니다. 동아대 국제교류처 또는 하이코리아(hikorea.go.kr)에 직접 문의 바랍니다." 라고만 답하세요.
3. 추측이나 외부 지식 사용 금지.
4. 한국어로만 답변하세요.
5. 3~6문장 이내로 간결하게 답하세요."""


class HFRuntimeClient:
    """HuggingFace 로컬 모델 기반 런타임 클라이언트."""

    def __init__(self, model: str | None = None) -> None:
        self._model_name = model or os.environ.get("HF_RUNTIME_MODEL", _DEFAULT_MODEL)
        self._pipe = None
        logger.info("HFRuntimeClient 초기화: %s (최초 질문 시 로드)", self._model_name)

    def _load(self) -> None:
        if self._pipe is not None:
            return

        import torch
        from transformers import pipeline

        logger.info("HF 모델 로드 중: %s ...", self._model_name)
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self._pipe = pipeline(
            "text-generation",
            model=self._model_name,
            dtype=dtype,
            device_map="auto",
        )
        logger.info("HF 모델 로드 완료")

    def _generate(self, user_text: str, max_new_tokens: int = 512) -> str:
        self._load()
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        try:
            out = self._pipe(
                messages,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=1.0,
                return_full_text=False,
            )
            # pipeline 반환 형식: [{"generated_text": str or [{"role":..,"content":..}]}]
            generated = out[0]["generated_text"]
            if isinstance(generated, list):
                # chat template 반환 시 마지막 assistant 메시지
                for msg in reversed(generated):
                    if msg.get("role") == "assistant":
                        return (msg.get("content") or "").strip()
                return ""
            return (generated or "").strip()
        except Exception as exc:
            logger.error("HF 생성 실패: %s", exc)
            return ""

    def is_available(self) -> bool:
        return True

    def close(self) -> None:
        self._pipe = None

    def normalize_question(self, question: str) -> str:
        # 로컬 테스트용 — 정규화 생략
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

        user_text = (
            f"[참조 문서]\n{context}\n\n"
            f"[질문]\n{question}"
        )
        answer = self._generate(user_text, max_new_tokens=512)
        return answer if answer else _STRICT_NO_ANSWER
