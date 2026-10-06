from __future__ import annotations

from yhs.rag.retrieval.translator import QueryTranslator, resolve_response_language


def test_question_language_wins_when_user_selected_it():
    assert resolve_response_language("What is the visa?", ["ko", "en"]) == "en"


def test_falls_back_to_primary_language_when_question_language_not_selected():
    assert resolve_response_language("What is the visa?", ["ko", "zh"]) == "ko"


def test_unsupported_selected_language_is_dropped():
    assert resolve_response_language("What is the visa?", ["vi", "en"]) == "en"


def test_no_selection_uses_question_language_default_ko():
    assert resolve_response_language("비자 연장 방법", None) == "ko"
    assert resolve_response_language("How do I extend my visa?", []) == "en"


def test_translate_answer_translates_each_line_and_keeps_blank_lines():
    t = QueryTranslator.__new__(QueryTranslator)
    calls: list[str] = []

    def fake_translate(text, target_lang, source_lang=None):
        calls.append(text)
        return f"[{text}]"

    t.translate = fake_translate
    assert t.translate_answer("가\n\n나", "en") == "[가]\n\n[나]"
    assert calls == ["가", "나"]
