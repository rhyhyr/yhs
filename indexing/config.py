"""인덱싱 설정/환경 모듈.

역할:
- .env 로딩 및 실행 환경 변수 초기화
- 인덱싱에 필요한 상수(경로, 모델, 임계값) 제공
- 실행 전 필수 키 검증 및 Gemini 모델 선택 함수 제공
"""

from __future__ import annotations

import os

import google.generativeai as genai


def load_env(path: str = ".env") -> None:
    """python-dotenv 없이 .env를 읽어 환경변수를 채운다."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)


load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.0-flash")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", os.environ.get("NEO4J_USERNAME", "neo4j"))
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

PDF_DIR = os.environ.get("PDF_DIR", os.path.join(os.path.expanduser("~"), "neo4j", "pdf"))

EMBED_MODEL = os.environ.get("EMBED_MODEL", "jhgan/ko-sroberta-multitask")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "380"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "76"))
SIM_THRESHOLD = float(os.environ.get("SIM_THRESHOLD", "0.27"))


def validate_env() -> None:
    """실행에 필요한 최소 환경변수 존재 여부를 검증한다."""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not NEO4J_PASSWORD:
        missing.append("NEO4J_PASSWORD")
    if missing:
        raise ValueError(
            f"\n[오류] .env에 다음 키가 없습니다: {', '.join(missing)}\n"
            ".env 파일 예시:\n"
            "  GEMINI_API_KEY=AIzaSy...\n"
            "  NEO4J_PASSWORD=your_password\n"
            "  PDF_DIR=C:\\\\Users\\\\사용자명\\\\Documents\\\\pdf\n"
        )


def build_gemini_model() -> genai.GenerativeModel:
    """사용 가능한 generateContent 모델 중 우선순위에 따라 선택한다."""
    preferred = [
        GEMINI_MODEL,
        "gemini-3.0-flash",
        "gemini-3-flash",
        "gemini-flash-latest",
    ]
    try:
        available = {
            m.name.replace("models/", ""): m
            for m in genai.list_models()
            if "generateContent" in (getattr(m, "supported_generation_methods", []) or [])
        }
        for name in preferred:
            if name in available:
                if name != GEMINI_MODEL:
                    print(f"[INFO] Gemini 모델 자동 선택: {name} (설정값: {GEMINI_MODEL})")
                return genai.GenerativeModel(name)
        if available:
            chosen = next(iter(available))
            print(f"[INFO] Gemini 모델 자동 선택(폴백): {chosen}")
            return genai.GenerativeModel(chosen)
    except Exception as e:
        print(f"[WARN] Gemini 모델 목록 조회 실패, 설정값 사용: {e}")
    return genai.GenerativeModel(GEMINI_MODEL)
