"""FAQ fast path 신뢰도 게이트 + query_runner fallthrough."""

import sys
from unittest.mock import MagicMock

import pytest

from yhs.rag.faq import FastPathHandler
from yhs.schema.types import RetrievalResult

# 평가셋에서 실제로 FAQ 오답이 나가던 문항 (cross_hop / dirty / 시점 의존)
WRONG_FAST_PATH = [
    "외국인등록하면 바로 은행 계좌 개설 가능해?",
    "D-4에서 D-2로 자격 바꾸면 외국인등록도 다시 해야 해?",
    "D-4에서 D-2로 비자 바꾸면 건강보험도 새로 가입해야 해?",
    "알바 허가 없이 그냥 하면 어케됨?",
    "D-4에서 D-2로 비자 바꿀 때 재정능력 증빙은 얼마야?",
    "대학원 유학생 장학금 유지 조건은?",
]


@pytest.mark.parametrize("q", WRONG_FAST_PATH)
def test_low_coverage_falls_back_to_rag(q):
    answer, m = FastPathHandler().match_with_score(q)
    assert answer is None
    assert m.reason == "low_coverage" and m.entry_index is not None


@pytest.mark.parametrize("q", ["유학생도 건강보험 가입 대상이야?", "외국인 유학생 장학금은 어떤 종류가 있어?"])
def test_simple_definition_still_answered(q):
    answer, m = FastPathHandler().match_with_score(q)
    assert answer and m.reason == "ok" and m.confidence == m.coverage == 1.0


def test_complex_gate_still_blocks():
    answer, m = FastPathHandler().match_with_score("건강보험 가입 방법")
    assert answer is None and m.reason == "complex_gate"


@pytest.fixture
def query_runner():
    # query_runner 는 conftest 가 mock 한 requests 로 llm 클라이언트들을 import 한다.
    # 그 캐시가 남으면 뒤의 test_ollama_integration 이 mock requests 를 물려받으므로 치운다.
    before = set(sys.modules)
    from yhs.rag import query_runner, runtime
    yield query_runner, runtime
    for name in set(sys.modules) - before:
        del sys.modules[name]


def test_process_question_runs_rag_when_faq_declines(query_runner):
    qr, runtime = query_runner
    engine = MagicMock()
    engine.retrieve.return_value = RetrievalResult(triples=[], chunks=[], retrieval_method="no_answer")
    engine.build_prompt_context.return_value = ""
    out = qr.process_question(
        WRONG_FAST_PATH[0], llm=None, engine=engine, web_client=MagicMock(),
        faq_handler=FastPathHandler(), thresholds=runtime.GateThresholds.from_config(),
    )
    assert out["path"] != "faq"
    engine.retrieve.assert_called()
