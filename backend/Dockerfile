# ─────────────────────────────────────────────────────────────────────────────
# yhs 백엔드 — FastAPI + Graph RAG
#
# 레이어 순서 원칙: 잘 안 바뀌는 것부터, 자주 바뀌는 것은 맨 뒤로.
#   의존성(느림, 수 GB) → 시스템 패키지 → 브라우저 → 앱 소스(빠름, 자주 바뀜)
#
# 특히 앱 설치를 builder 가 아니라 런타임 단계 맨 끝에서 한다.
# builder 안에서 앱을 설치하면 소스를 한 줄만 고쳐도 /opt/venv 가 바뀌고,
# 그러면 `COPY --from=builder /opt/venv`(GPU 빌드 기준 13GB)가 통째로
# 다시 복사된다. 이 순서면 소스 변경 시 마지막 작은 레이어만 다시 만들어진다.
# ─────────────────────────────────────────────────────────────────────────────

# ── 1단계: 의존성만 담은 venv 만들기 ──────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# 의존성 목록과 설정 YAML 만 복사한다. 소스는 넣지 않는다 —
# 이 단계의 결과물은 "의존성이 설치된 venv" 이고, 소스와 무관해야 한다.
# config/ 는 pyproject 의 force-include 대상이라 빌드 시점에 반드시 있어야 한다.
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
# GPU 로 빌드:  ./scripts/dev.sh up-gpu
ARG TORCH_VARIANT=cpu
ARG TORCH_CPU_INDEX=https://download.pytorch.org/whl/cpu
ARG TORCH_GPU_INDEX=https://download.pytorch.org/whl/cu126

# 껍데기 패키지로 의존성만 설치한다 (소스는 런타임 단계에서 넣는다).
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
      # bitsandbytes 4-bit 양자화가 triton 을 쓰는데, triton 은 커널을 런타임에
      # JIT 컴파일한다. 컴파일러가 없으면 "Failed to find C compiler" 로 죽고,
      # 추출기가 그 예외를 삼켜 엔티티·관계 0건이라는 조용한 실패가 된다.
      gcc g++ \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
      libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 여기서부터가 무거운 레이어. 소스와 무관하므로 캐시가 오래 유지된다.
COPY --from=builder /opt/venv /opt/venv

RUN playwright install chromium \
 && useradd --create-home --uid 10001 app \
 && chown -R app:app /opt/playwright \
 # HF 캐시 디렉토리를 미리 만들고 app 소유로 둔다.
 #
 # compose 가 여기에 named volume 을 붙이는데, 이미지에 디렉토리가 없으면
 # 도커가 root 소유로 만들어 버린다. 그러면 비특권 사용자로 도는 프로세스가
 # 모델을 내려받지 못하고 "PermissionError ... Check cache directory
 # permissions" 로 죽는다. 인제스트에서는 이게 조용한 실패로 나타났다 —
 # LLM 추출이 전부 실패했는데 규칙 기반 폴백이 동작해 트리플만 0건이 됐다.
 && mkdir -p /home/app/.cache/huggingface \
 && chown -R app:app /home/app/.cache

# ── 앱 소스 (자주 바뀜 — 반드시 맨 뒤) ────────────────────────────────────────
# 여기만 다시 만들어지므로 소스 수정 후 재빌드가 수 초에 끝난다.
COPY pyproject.toml README.md /src/
COPY config /src/config
COPY src /src/src
RUN /opt/venv/bin/pip install --no-deps --force-reinstall /src \
 && rm -rf /src

WORKDIR /app
USER app

EXPOSE 8000

# /health 는 리소스 초기화가 끝났는지도 알려준다 (status: starting|ok).
# 임베딩 모델 로딩이 오래 걸리므로 start-period 를 넉넉히 잡는다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "yhs.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
