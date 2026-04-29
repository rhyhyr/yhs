"""
graph_rag/pipeline/cleaner.py

역할:
- 원시 텍스트의 공백 정리, 특수문자 제거, 불필요한 줄바꿈 정규화
- 규칙 기반으로만 처리 (LLM 불필요)
"""

from __future__ import annotations

import re


# 제거 대상 특수문자 (의미 있는 기호 ·、。 는 보존)
_STRIP_RE = re.compile(r"[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ\-·,.()%/&@#:\[\]\{\}\"\'?!~]")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """
    텍스트를 정제한다.
    1. 이상한 공백 문자(탭, NBSP 등) 통일
    2. 연속 공백 축소
    3. 3줄 이상 연속 줄바꿈 → 2줄로 축소
    4. 앞뒤 공백 제거
    """
    # 탭·NBSP 등 → 공백
    text = text.replace("\t", " ").replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # 연속 공백 축소
    text = _MULTI_SPACE.sub(" ", text)
    # 연속 줄바꿈 축소
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()
