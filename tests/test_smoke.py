"""
Smoke tests — CI matrix가 돌릴 가벼운 테스트.

실제 RAG/에이전트 기능을 테스트하기보단, 다음을 검증합니다:
  - 환경에서 Python 표준 라이브러리가 정상 동작하는가
  - 환경변수가 의도대로 주입되는가 (CI에서 secrets 동작 확인용)

Why so simple?
  Week 7 과제는 'CI/CD 파이프라인 자체'를 검증하는 것이므로,
  테스트는 무거우면 안 됩니다 (matrix가 6개 조합 = OS 2 × Python 3).
"""

import os
import sys


def test_python_version():
    """Python이 3.10 이상에서 실행 중인지 확인."""
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version_info}"


def test_basic_arithmetic():
    """Sanity check — 진짜 기본."""
    assert 1 + 1 == 2
    assert "yhs" + "_test" == "yhs_test"


def test_environment_marker():
    """
    CI 환경에서 실행 중인지 확인.
    GitHub Actions는 항상 CI=true 환경변수를 주입합니다.
    로컬 실행 시에는 이 검증을 건너뜁니다.
    """
    if os.getenv("GITHUB_ACTIONS") == "true":
        assert os.getenv("CI") == "true", "CI env var should be 'true' on GitHub Actions"


def test_secret_injection_pattern():
    """
    Secrets 주입 패턴 확인 — 키가 없어도 fallback으로 안전하게 동작해야 함.

    이 테스트는 secret이 없어도 통과합니다 (실제 키 검증 X).
    실제 코드에서 'API 키 없으면 안전한 기본값'을 쓰는 패턴을 보여주는 예시.
    """
    api_key = os.getenv("DEMO_API_KEY", "demo-fallback")
    assert api_key, "API key should never be empty (fallback should kick in)"
    assert len(api_key) > 0


def test_imports_smoke():
    """주요 표준 라이브러리 import — Python 환경 정상 여부 확인."""
    import json  # noqa: F401
    import pathlib  # noqa: F401
    import typing  # noqa: F401

    assert True