"""
yhs/ingest/llm/exaone_kb_client.py

역할:
- HuggingFace로 로컬에 설치된 EXAONE 3.5로 엔티티·관계를 추출한다.
- 완전 무료, 인터넷 불필요, 속도 제한 없음.

전제:
    EXAONE 모델이 HuggingFace 캐시에 있어야 함
    (~/.cache/huggingface/hub/models--LGAI-EXAONE--EXAONE-3.5-7.8B-Instruct)

사용:
    .env에 LLM_PROVIDER=exaone 설정
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from yhs.ingest.llm.json_repair import parse_json_with_repair
from yhs.ingest.llm.prompts import EXTRACTION_SYSTEM_PROMPT
from yhs.ingest.stats import STATS

logger = logging.getLogger(__name__)

def _model_name() -> str:
    """추출 모델 이름 (KB_LLM_MODEL 환경변수로 교체 가능)."""
    from yhs.core.settings import get_settings

    return get_settings().kb_llm_model

# 프롬프트는 provider 공용이다 (yhs/ingest/llm/prompts.py).
# provider 마다 따로 들고 있으면 반드시 어긋난다.
_SYSTEM_PROMPT = EXTRACTION_SYSTEM_PROMPT


class ExaoneKBClient:
    """로컬 EXAONE HuggingFace 모델 기반 KB 추출 클라이언트."""

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None

    def _load_model(self) -> None:
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = _model_name()
        logger.info("EXAONE 모델 로드 중: %s (최초 1회)", model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
        )

        # VRAM 체크 후 자동으로 로드 방식 결정
        use_4bit = False
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            use_4bit = vram_gb < 14  # 14GB 미만이면 4-bit 양자화
            logger.info("GPU VRAM: %.1f GB → %s", vram_gb, "4-bit 양자화" if use_4bit else "bfloat16")

        if use_4bit:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(load_in_4bit=True)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
        self._model.eval()
        logger.info("EXAONE 모델 로드 완료")

    def _generate(self, user_text: str) -> str:
        self._load_model()

        import torch

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        # EXAONE 채팅 템플릿 적용
        input_ids = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda" if torch.cuda.is_available() else "cpu")

        with torch.no_grad():
            output = self._model.generate(
                input_ids,
                max_new_tokens=2048,
                do_sample=False,       # 그리디 디코딩 → JSON 일관성 높음
                temperature=1.0,
                eos_token_id=self._tokenizer.eos_token_id,
            )

        # 입력 부분 제거하고 생성된 텍스트만 추출
        generated = output[0][input_ids.shape[-1]:]
        return self._tokenizer.decode(generated, skip_special_tokens=True).strip()

    def extract_entities_and_relations(
        self, text: str, source_file: str = ""
    ) -> dict[str, Any]:
        """
        텍스트에서 엔티티와 관계를 추출한다.
        Returns: {"entities": [...], "relations": [...]}
        """
        user_text = (
            f"[출처: {source_file}]\n\n"
            f"다음 텍스트에서 엔티티와 관계를 추출하세요:\n\n{text[:1500]}"
        )

        try:
            raw = self._generate(user_text)

            # JSON 블록만 추출 (앞뒤 설명 텍스트 제거)
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            # { } 사이만 추출
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            # 로컬 모델은 긴 출력에서 JSON 을 자주 깨뜨린다
            # (따옴표 누락, 끝 잘림). 통째로 버리기 전에 복구를 시도한다.
            result, repaired = parse_json_with_repair(raw)
            if result is None:
                logger.error("EXAONE JSON 파싱 및 복구 모두 실패 — 해당 청크 건너뜀")
                return {"entities": [], "relations": []}
            if repaired:
                STATS.json_repaired += 1
                logger.info('JSON 복구 성공 (%d자)', len(raw))
            return result

        except Exception as exc:
            import traceback
            logger.error("EXAONE 추출 실패: %s\n%s", exc, traceback.format_exc())
            return {"entities": [], "relations": []}

    def parse_flowchart_image(self, image_path: Path) -> dict[str, Any]:
        """Vision 미지원 — 빈 결과 반환."""
        logger.warning("EXAONE은 이미지 파싱을 지원하지 않습니다: %s", image_path)
        return {"entities": [], "relations": []}
