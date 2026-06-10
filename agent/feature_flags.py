"""
Week11 - 환경변수 기반 Feature Flag 시스템

사용법:
    from agent.feature_flags import flags

    if flags.is_enabled("ENABLE_GRAPH_SEARCH"):
        ...

    variant = flags.get_variant("AB_RESPONSE_FORMAT", default="control")
"""
import os


class FeatureFlags:
    @staticmethod
    def is_enabled(flag_name: str) -> bool:
        """플래그가 'true'(대소문자 무관)이면 True 반환"""
        return os.getenv(flag_name, "false").strip().lower() == "true"

    @staticmethod
    def get_variant(flag_name: str, default: str = "control") -> str:
        """A/B variant 값 반환. 미설정 시 default 반환"""
        return os.getenv(flag_name, default)


flags = FeatureFlags()

# ──────────────────────────────────────────────
# 등록된 Feature Flag 목록 (문서화 목적)
# ──────────────────────────────────────────────
REGISTERED_FLAGS = {
    # Feature Flags (on/off)
    "ENABLE_GRAPH_SEARCH":   "Neo4j 그래프 검색 활성화",
    "ENABLE_HYBRID_MODE":    "벡터+그래프 하이브리드 검색 모드",
    "ENABLE_RISK_FILTER":    "리스크 최소화 응답 필터링",

    # A/B 테스트 Variants
    "AB_RESPONSE_FORMAT":    "응답 포맷 실험 (control | verbose)",
    "AB_SEARCH_ALGORITHM":   "검색 알고리즘 실험 (vector | hybrid)",
}
