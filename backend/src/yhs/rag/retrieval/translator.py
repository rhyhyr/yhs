"""
agent/retrieval/translator.py

역할:
  중국어 질문을 한국어로 번역하여 기존 파이프라인이 그대로 동작하게 한다.

동작 원리:
  1. langdetect로 입력 언어를 감지한다.
  2. 중국어(간체·번체)가 감지되면 Helsinki-NLP/opus-mt-zh-ko 로컬 모델로 번역한다.
  3. 한국어·영어 등 나머지 언어는 그대로 반환한다.
  4. 번역 결과는 메모리 캐시에 저장하여 동일 질문이 들어오면 재번역하지 않는다.

비용: API 호출 없음 (모델 로컬 실행, 약 300MB 다운로드 1회)
속도: CPU 기준 짧은 문장 ~0.3초, GPU 있으면 더 빠름

설치:
  pip install langdetect sentencepiece
  (transformers는 sentence-transformers 의존성으로 이미 설치됨)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# 번역 대상 언어 코드 (langdetect 기준)
_ZH_LANGS = {"zh-cn", "zh-tw", "zh"}
_ZH_KO_MODEL = "Helsinki-NLP/opus-mt-zh-ko"

# langdetect는 기본적으로 non-deterministic → seed 고정으로 일관성 보장
try:
    from langdetect import DetectorFactory
    DetectorFactory.seed = 42
except ImportError:
    pass  # 설치 안 됐으면 detect 호출 시 에러


def _detect_lang(text: str) -> str:
    """
    입력 텍스트의 언어 코드를 반환한다.
    - 텍스트가 너무 짧으면 (5자 미만) 'unknown' 반환 → 원문 그대로 사용
    - langdetect 미설치 또는 감지 실패 시 'unknown' 반환
    """
    if len(text.strip()) < 5:
        return "unknown"
    try:
        from langdetect import detect
        return detect(text)
    except Exception as exc:
        logger.debug("언어 감지 실패 (원문 사용): %s", exc)
        return "unknown"


class QueryTranslator:
    """
    한국어가 아닌 질문을 한국어로 번역하는 레이어.

    현재 지원:
      - 중국어(간체·번체) → 한국어: Helsinki-NLP/opus-mt-zh-ko

    설계 원칙:
      - 모델은 첫 번역 요청 시에만 로드 (lazy loading)
        → 서버 시작 속도에 영향 없음
      - 동일 질문은 캐시에서 반환
        → 같은 질문 반복 시 번역 비용 0
      - 번역 실패 시 원문 그대로 반환
        → 파이프라인 중단 없음
    """

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._cache: dict[str, str] = {}  # {원문: 번역문}

    # ── 모델 로드 (첫 번역 시 1회) ───────────────────────────────────────────
    def _load_model(self) -> None:
        """번역 모델을 메모리에 올린다. 이미 로드됐으면 바로 반환."""
        if self._model is not None:
            return
        try:
            from transformers import MarianMTModel, MarianTokenizer
            logger.info("번역 모델 로드 시작: %s (최초 1회, 약 300MB)", _ZH_KO_MODEL)
            self._tokenizer = MarianTokenizer.from_pretrained(_ZH_KO_MODEL)
            self._model = MarianMTModel.from_pretrained(_ZH_KO_MODEL)
            logger.info("번역 모델 로드 완료")
        except ImportError:
            raise ImportError(
                "번역 모델 실행에 필요한 패키지가 없습니다.\n"
                "pip install transformers sentencepiece"
            )
        except Exception as exc:
            logger.error("번역 모델 로드 실패: %s", exc)
            raise

    # ── 실제 번역 ────────────────────────────────────────────────────────────
    def _do_translate(self, text: str) -> str:
        """중국어 텍스트를 한국어로 번역한다."""
        self._load_model()
        inputs = self._tokenizer(
            [text],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,     # 유학생 질문은 대부분 짧음, 256으로 충분
        )
        outputs = self._model.generate(
            **inputs,
            num_beams=4,        # beam search: 번역 품질 vs 속도 균형
            max_length=256,
        )
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

    # ── 메인 인터페이스 ──────────────────────────────────────────────────────
    def translate_if_needed(self, text: str) -> tuple[str, bool]:
        """
        번역이 필요한 질문이면 번역하고, 아니면 원문을 그대로 반환한다.

        Returns:
            (결과 텍스트, 번역됐으면 True / 원문이면 False)

        사용 예:
            korean, was_translated = translator.translate_if_needed("我的签证怎么延长？")
            # korean  = "내 비자는 어떻게 연장하나요?"
            # was_translated = True
        """
        # 캐시 히트
        if text in self._cache:
            cached = self._cache[text]
            return cached, cached != text

        lang = _detect_lang(text)
        logger.debug("언어 감지: [%s] '%s'", lang, text[:40])

        if lang in _ZH_LANGS:
            try:
                translated = self._do_translate(text)
                logger.info(
                    "중국어 번역 완료: '%s' → '%s'",
                    text[:40], translated[:40],
                )
                self._cache[text] = translated
                return translated, True
            except Exception as exc:
                # 번역 실패해도 파이프라인 멈추지 않음
                logger.warning("번역 실패, 원문으로 진행: %s", exc)
                self._cache[text] = text
                return text, False

        # 한국어, 영어 등 → 번역 불필요
        self._cache[text] = text
        return text, False


# ── 싱글턴 인스턴스 ────────────────────────────────────────────────────────────
# 모든 곳에서 동일한 인스턴스를 공유하여 모델 중복 로드와 캐시 낭비를 방지한다.
_translator: QueryTranslator | None = None


def get_translator() -> QueryTranslator:
    """싱글턴 QueryTranslator를 반환한다."""
    global _translator
    if _translator is None:
        _translator = QueryTranslator()
    return _translator


def is_translation_enabled() -> bool:
    """
    환경변수 ENABLE_ZH_TRANSLATION으로 번역 기능을 on/off할 수 있다.
    기본값 True (번역 활성화).
    성능 비교 실험 시 False로 설정하면 번역 없이 원문이 그대로 파이프라인에 들어간다.

    사용:
        ENABLE_ZH_TRANSLATION=false python experiments/zh_eval.py
    """
    import os
    return os.getenv("ENABLE_ZH_TRANSLATION", "true").strip().lower() != "false"
