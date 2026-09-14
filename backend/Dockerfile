# ─────────────────────────────────────────────────────────────────────────────
# yhs 백엔드 — FastAPI + Graph RAG
#
# 멀티스테이지로 나눈 이유:
#   의존성 설치(느림, 잘 안 바뀜)와 소스 복사(빠름, 자주 바뀜)를 다른 레이어로
#   두면 코드만 고쳤을 때 pip install 을 다시 돌리지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

# ── 1단계: 의존성 빌드 ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# 의존성 목록과 설정 YAML 을 먼저 복사한다.
# config/ 는 pyproject 의 force-include 대상이라 빌드 시점에 반드시 있어야 한다.
# 소스(src/)는 아직 넣지 않아, 코드만 고쳤을 때 이 레이어 캐시가 살아 있다.
COPY pyproject.toml README.md ./
COPY config ./config
# torch 빌드 선택: cpu(기본) | gpu
#   cpu — PyTorch CPU 인덱스. 이미지가 3~4GB 작고 어디서나 돈다.
#         CI 와 GPU 없는 서버의 기본값.
#   gpu — PyTorch CUDA 인덱스(cu126). 임베딩과 로컬 LLM 추론이 GPU 로 돌아간다.
#
# 기본 PyPI 의 torch 를 그냥 받지 않는 이유:
#   torch 2.14 는 PyPI 에서 cuda-toolkit 13 메타패키지를 extras 째로 끌어와
#   설치 중 메모리를 크게 먹고(빌드가 OOM 으로 SIGKILL 됨) 이미지도 더 커진다.
#   PyTorch 전용 인덱스는 필요한 휠만 담은 일관된 세트를 준다.
#
# GPU 로 빌드:
#   make up-gpu
ARG TORCH_VARIANT=cpu
ARG TORCH_CPU_INDEX=https://download.pytorch.org/whl/cpu
ARG TORCH_GPU_INDEX=https://download.pytorch.org/whl/cu126

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && if [ "$TORCH_VARIANT" = "cpu" ]; then \
      TORCH_INDEX="$TORCH_CPU_INDEX"; \
    else \
      TORCH_INDEX="$TORCH_GPU_INDEX"; \
    fi \
 && /opt/venv/bin/pip install --index-url "$TORCH_INDEX" "torch" \
 && mkdir -p src/yhs && touch src/yhs/__init__.py \
 && /opt/venv/bin/pip install .

# 이제 실제 소스를 넣고 패키지만 다시 설치 (무거운 의존성은 이미 위에서 설치됨).
# --force-reinstall 이 없으면 pip 가 "이미 설치됨" 으로 건너뛰어
# 껍데기 __init__.py 가 그대로 남는다.
COPY src ./src
RUN /opt/venv/bin/pip install --no-deps --force-reinstall .


# ── 2단계: 런타임 ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Playwright 브라우저를 루트가 아닌 위치에 두어 비특권 사용자도 읽게 한다
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    HF_HOME=/home/app/.cache/huggingface

# Playwright(Chromium) 실행에 필요한 시스템 라이브러리.
# 크롤러가 JS 렌더링 페이지를 읽을 때 사용한다.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
      libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

RUN playwright install chromium \
 && useradd --create-home --uid 10001 app \
 && chown -R app:app /opt/playwright

WORKDIR /app
USER app

EXPOSE 8000

# /health 는 리소스 초기화가 끝났는지도 알려준다 (status: starting|ok).
# 임베딩 모델 로딩이 오래 걸리므로 start-period 를 넉넉히 잡는다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "yhs.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
