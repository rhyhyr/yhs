"""
Week12 - Feature Flags 단위 테스트
TDD Red-Green-Refactor 사이클로 작성
"""
import os

import pytest

from agent.feature_flags import FeatureFlags

flags = FeatureFlags()


def test_flag_default_is_false():
    os.environ.pop("TEST_FLAG_DUMMY", None)
    assert flags.is_enabled("TEST_FLAG_DUMMY") is False


def test_flag_enabled_when_true():
    os.environ["TEST_FLAG_DUMMY"] = "true"
    assert flags.is_enabled("TEST_FLAG_DUMMY") is True
    del os.environ["TEST_FLAG_DUMMY"]


@pytest.mark.parametrize("value", ["TRUE", "True", "TRUE "])
def test_flag_case_insensitive(value):
    os.environ["TEST_FLAG_DUMMY"] = value
    assert flags.is_enabled("TEST_FLAG_DUMMY") is True
    del os.environ["TEST_FLAG_DUMMY"]


@pytest.mark.parametrize("value", ["false", "0", "", "no"])
def test_flag_disabled_values(value):
    os.environ["TEST_FLAG_DUMMY"] = value
    assert flags.is_enabled("TEST_FLAG_DUMMY") is False
    del os.environ["TEST_FLAG_DUMMY"]


def test_variant_returns_default():
    os.environ.pop("AB_TEST_DUMMY", None)
    assert flags.get_variant("AB_TEST_DUMMY", "control") == "control"


def test_variant_returns_env_value():
    os.environ["AB_TEST_DUMMY"] = "variant_b"
    assert flags.get_variant("AB_TEST_DUMMY") == "variant_b"
    del os.environ["AB_TEST_DUMMY"]


def test_multiple_flags_independent():
    os.environ["FLAG_A"] = "true"
    os.environ["FLAG_B"] = "false"
    assert flags.is_enabled("FLAG_A") is True
    assert flags.is_enabled("FLAG_B") is False
    del os.environ["FLAG_A"]
    del os.environ["FLAG_B"]
