"""
Smoke tests — CI matrix used to validate the pipeline.

These tests check:
  - Python standard library is functional
  - Environment/secrets injection works (with safe fallback)

Why so simple?
  Week 7 assignment validates the CI/CD pipeline itself,
  so tests should be lightweight (matrix runs 6 combos).
"""

import os
import sys


def test_python_version():
    """Python should be 3.10 or newer."""
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version_info}"


def test_basic_arithmetic():
    """Sanity check."""
    assert 1 + 1 == 2
    assert "yhs" + "_test" == "yhs_test"


def test_environment_marker():
    """
    On GitHub Actions, CI env var is always 'true'.
    Skipped when running locally.
    """
    if os.getenv("GITHUB_ACTIONS") == "true":
        assert os.getenv("CI") == "true", "CI env var should be 'true' on GitHub Actions"


def test_secret_injection_pattern():
    """
    Verify the safe-fallback pattern for secrets.

    NOTE: os.getenv(name, default) returns the default ONLY when the env var
    is not set at all. If the env var is set to an empty string (which happens
    when a GitHub secret is unregistered), os.getenv returns "" — not the default.
    So we use 'or' to coalesce empty string to the fallback.
    """
    api_key = os.getenv("DEMO_API_KEY") or "demo-fallback"
    assert api_key, "API key should never be empty (fallback should kick in)"
    assert len(api_key) > 0


def test_imports_smoke():
    """Standard library imports should work."""
    import json  # noqa: F401
    import pathlib  # noqa: F401
    import typing  # noqa: F401

    assert True