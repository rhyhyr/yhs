"""
yhs/rag/retrieval/translator.py

Multilingual translation layer for retrieval and final answers.

The knowledge base is mostly Korean, so non-Korean questions are translated to
Korean before entity linking and vector search. Final answers can then be
translated back to the configured response language.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_SUPPORTED_LANGS = {"ko", "en", "zh"}
_NLLB_CODES = {
    "ko": "kor_Hang",
    "en": "eng_Latn",
    "zh": "zho_Hans",
}

try:
    from langdetect import DetectorFactory

    DetectorFactory.seed = 42
except ImportError:
    pass


def normalize_language(lang: str | None, default: str = "ko") -> str:
    """Return one of ko/en/zh for user-facing language settings."""
    if not lang:
        return default
    value = lang.strip().lower().replace("_", "-")
    if value in {"ko", "kor", "korean", "kr"}:
        return "ko"
    if value in {"en", "eng", "english"}:
        return "en"
    if value in {"zh", "zh-cn", "zh-hans", "zh-tw", "zh-hant", "cn", "chinese"}:
        return "zh"
    return default


def _detect_lang(text: str) -> str:
    """
    Detect the input language as ko/en/zh/unknown.

    Regex comes first so the service still works when langdetect is not
    installed in a local development environment.
    """
    stripped = text.strip()
    if len(stripped) < 2:
        return "unknown"

    has_hangul = bool(re.search(r"[\uac00-\ud7a3]", stripped))
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", stripped))
    if has_hangul:
        return "ko"
    if has_cjk:
        return "zh"

    try:
        from langdetect import detect

        return normalize_language(detect(stripped), default="unknown")
    except Exception as exc:
        logger.debug("Language detection failed; falling back to English: %s", exc)
        return "en" if re.search(r"[A-Za-z]", stripped) else "unknown"


class QueryTranslator:
    """
    Translate between Korean, English, and Chinese with one NLLB model.

    Default model: facebook/nllb-200-distilled-600M. It is larger than the old
    zh-ko Helsinki model, but gives one consistent multilingual path for
    en/zh/ko and supports answer translation as well as query translation.
    """

    def __init__(self, model_name: str | None = None) -> None:
        from yhs.core.settings import get_settings

        self._model_name = model_name or get_settings().translation_model
        self._tokenizer = None
        self._model = None
        self._cache: dict[tuple[str, str, str], str] = {}

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info("Loading translation model: %s", self._model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name)
            logger.info("Translation model loaded")
        except ImportError:
            raise ImportError(
                "Translation requires transformers and sentencepiece. "
                "Install backend dependencies with: pip install -e '.[dev]'"
            ) from None

    def detect_language(self, text: str) -> str:
        return _detect_lang(text)

    def translate(self, text: str, target_lang: str, source_lang: str | None = None) -> str:
        """Translate text to target_lang. Unsupported or same-language text is returned as-is."""
        source = normalize_language(source_lang or _detect_lang(text), default="unknown")
        target = normalize_language(target_lang, default=source if source in _SUPPORTED_LANGS else "ko")

        if source == target or source not in _SUPPORTED_LANGS or target not in _SUPPORTED_LANGS:
            return text

        key = (source, target, text)
        if key in self._cache:
            return self._cache[key]

        try:
            self._load_model()
            src_code = _NLLB_CODES[source]
            tgt_code = _NLLB_CODES[target]

            self._tokenizer.src_lang = src_code
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            forced_bos_token_id = self._tokenizer.convert_tokens_to_ids(tgt_code)
            outputs = self._model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                num_beams=4,
                max_length=512,
            )
            translated = self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            result = translated or text
            self._cache[key] = result
            return result
        except Exception as exc:
            logger.warning(
                "Translation failed (%s -> %s); using original text: %s",
                source,
                target,
                exc,
            )
            self._cache[key] = text
            return text

    def translate_if_needed(self, text: str) -> tuple[str, bool]:
        """
        Translate non-Korean queries to Korean for retrieval.

        Returns (text_for_search, was_translated).
        """
        source = _detect_lang(text)
        if source == "ko" or source not in _SUPPORTED_LANGS:
            return text, False

        translated = self.translate(text, "ko", source_lang=source)
        return translated, translated != text

    def translate_answer(self, text: str, target_lang: str, source_lang: str = "ko") -> str:
        """
        Translate a Korean answer to the response language, line by line.

        NLLB truncates input at 512 tokens, so long answers are split on newlines.
        # ponytail: a single line over 512 tokens is still cut, split on sentences if that shows up
        """
        return "\n".join(
            self.translate(line, target_lang, source_lang=source_lang) if line.strip() else line
            for line in text.split("\n")
        )


_translator: QueryTranslator | None = None


def get_translator() -> QueryTranslator:
    global _translator
    if _translator is None:
        _translator = QueryTranslator()
    return _translator


def is_translation_enabled() -> bool:
    from yhs.core.settings import get_settings

    return get_settings().enable_zh_translation


def resolve_response_language(question: str, user_languages: list[str] | None = None) -> str:
    """
    Pick the answer language for one question.

    The question's language wins when the user selected it; otherwise the first
    selected language is used. Unsupported codes (e.g. vi) are dropped. With no
    usable selection, the question's own language is used, defaulting to Korean.
    """
    selected = [normalize_language(lang, default="") for lang in user_languages or []]
    selected = [lang for lang in dict.fromkeys(selected) if lang in _SUPPORTED_LANGS]
    detected = _detect_lang(question)
    if not selected:
        return detected if detected in _SUPPORTED_LANGS else "ko"
    return detected if detected in selected else selected[0]
