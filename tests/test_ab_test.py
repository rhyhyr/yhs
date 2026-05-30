"""
Week12 - A/B 테스트 단위 테스트
"""
import json
import os

import pytest

from agent.ab_test import assign_variant, track_event


def test_variant_consistency():
    v1 = assign_variant("user_001", "format_test", ["control", "verbose"])
    v2 = assign_variant("user_001", "format_test", ["control", "verbose"])
    assert v1 == v2


def test_variant_in_list():
    variants = ["A", "B", "C"]
    result = assign_variant("user_xyz", "algo_test", variants)
    assert result in variants


def test_variant_distribution():
    results = [assign_variant(f"u{i}", "exp", ["A", "B"]) for i in range(1000)]
    a_count = results.count("A")
    assert 350 < a_count < 650, f"분포 이상: A={a_count}/1000"


def test_different_experiments_independent():
    v1 = assign_variant("user_001", "exp_format", ["X", "Y"])
    v2 = assign_variant("user_001", "exp_algo", ["X", "Y"])
    assert v1 in ["X", "Y"]
    assert v2 in ["X", "Y"]


def test_track_event_creates_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    entry = track_event("u1", "exp_format", "control", "query_submitted")
    assert entry["user_id"] == "u1"
    assert entry["experiment"] == "exp_format"
    assert entry["variant"] == "control"
    assert entry["event"] == "query_submitted"

    log_file = tmp_path / "logs" / "ab_events.jsonl"
    assert log_file.exists()
    with open(log_file) as f:
        saved = json.loads(f.readline())
    assert saved["event"] == "query_submitted"
