"""
graph_rag/llm/ollama_kb_client.py

역할:
- KB 구축 단계에서 EXAONE(Ollama) 로컬 모델로 엔티티·관계를 추출한다.
- 완전 무료, API 한도 없음, 응답 잘림 없음.
- Ollama의 format=json 옵션으로 JSON 출력을 강제한다.

사용:
    LLM_PROVIDER=ollama 환경변수 설정 후 인제스트 실행

전제:
    Ollama가 실행 중이어야 함 (ollama serve)
    EXAONE 모델이 설치되어 있어야 함 (ollama pull exaone3.5:7b)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

import requests

from graph_rag.config import (
    ALLOWED_PREDICATES,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = f"""당신은 행정 문서에서 엔티티와 관계를 추출하는 전문가입니다.

규칙:
1. 반드시 JSON 형식으로만 출력하세요.
2. predicate는 반드시 아래 목록 중 하나여야 합니다:
   {', '.join(ALLOWED_PREDICATES)}
3. 조건문은 엣지의 condition 필드에 저장하세요.
4. confidence는 [0.7, 1.0] 범위로 표현하세요.
5. 확실하지 않은 항목은 포함하지 마세요.

출력 형식:
{{
  "entities": [
    {{"id": "고유식별자", "name": "표준명칭", "domain": "visa|health_insurance|part_time|school_admin|daily_life", "summary": "1-2문장 요약", "confidence": 0.9}}
  ],
  "relations": [
    {{"subject_id": "주체ID", "predicate": "관계타입", "object_id": "대상ID", "condition": "조건(없으면 빈문자열)", "confidence": 0.8}}
  ]
}}"""


class OllamaKBClient:
    """KB 구축용 Ollama(EXAONE) 로컬 클라이언트."""

    def __init__(self) -> None:
        self._base_url = OLLAMA_BASE_URL.rstrip("/")
        self._model = OLLAMA_MODEL
        self._api_url = f"{self._base_url}/api/generate"
        self._session = requests.Session()
        logger.info("OllamaKBClient 초기화: %s / %s", self._base_url, self._model)

    def _call(self, prompt: str) -> str:
        """Ollama API 호출. format=json으로 JSON 출력 강제."""
        payload = {
            "model": self._model,
            "system": _SYSTEM_PROMPT,
            "prompt": prompt,
            "format": "json",   # JSON 모드: 잘림 없이 완전한 JSON 반환
            "stream": False,
            "options": {
                "num_predict": 4096,
                "temperature": 0.1,
            },
        }
        try:
            resp = self._session.post(
                self._api_url, json=payload, timeout=OLLAMA_TIMEOUT
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Ollama 서버에 연결할 수 없습니다. 'ollama serve' 실행 여부 확인: {self._base_url}"
            )
        except Exception as exc:
            logger.error("Ollama 호출 실패: %s", exc)
            raise

    def extract_entities_and_relations(
        self, text: str, source_file: str = ""
    ) -> Dict[str, Any]:
        """
        텍스트에서 엔티티와 관계를 추출한다.
        Returns: {"entities": [...], "relations": [...]}
        """
        prompt = (
            f"[출처: {source_file}]\n\n"
            f"다음 텍스트에서 엔티티와 관계를 추출하세요:\n\n{text[:1500]}"
        )

        try:
            raw = self._call(prompt)
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Ollama JSON 파싱 실패: %s", exc)
            return {"entities": [], "relations": []}
        except Exception as exc:
            logger.error("Ollama 추출 실패: %s", exc)
            return {"entities": [], "relations": []}

    def parse_flowchart_image(self, image_path: Path) -> Dict[str, Any]:
        """Ollama는 Vision 미지원 — 빈 결과 반환."""
        logger.warning("Ollama는 이미지 파싱을 지원하지 않습니다: %s", image_path)
        return {"entities": [], "relations": []}
