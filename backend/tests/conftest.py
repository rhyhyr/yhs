"""
pytest 공통 설정.

src 레이아웃(`pythonpath = ["src"]`, backend/pyproject.toml)을 쓰므로
sys.path 조작은 하지 않는다.

무거운 외부 의존성(neo4j 드라이버, sentence-transformers, faiss 등)만
MagicMock으로 대체해 설치 없이도 단위 테스트가 돌아가게 한다.
yhs.* 내부 모듈은 절대 mock하지 않는다 — 그걸 검증하는 게 테스트이므로.
"""

import sys
import types
from unittest.mock import MagicMock

# ── 외부 패키지만 mock ────────────────────────────────────────────────────
MOCK_MODULES = [
    "google",
    "google.genai",
    "google.genai.types",
    "neo4j",
    "sentence_transformers",
    "faiss",
    "langchain",
    "langchain_community",
    "langchain_openai",
    "langchain_text_splitters",
    "pdfplumber",
    "pypdf",
    "openai",
    "sklearn",
    "sklearn.metrics",
    "sklearn.metrics.pairwise",
    "numpy",
    "bs4",
    "requests",
]

for _mod in MOCK_MODULES:
    sys.modules.setdefault(_mod, MagicMock())

# neo4j.exceptions 는 `except ClientError` 처럼 실제 예외 클래스가 필요하다.
# MagicMock은 except 절에 쓸 수 없으므로 진짜 클래스로 채운다.
if not isinstance(sys.modules.get("neo4j.exceptions"), types.ModuleType):
    _exc = types.ModuleType("neo4j.exceptions")
    _exc.ClientError = type("ClientError", (Exception,), {})
    _exc.ServiceUnavailable = type("ServiceUnavailable", (Exception,), {})
    _exc.Neo4jError = type("Neo4jError", (Exception,), {})
    sys.modules["neo4j.exceptions"] = _exc
