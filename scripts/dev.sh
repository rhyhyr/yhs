#!/usr/bin/env bash
#
# yhs 개발·실행 명령 모음 (macOS / Linux / Git Bash).
#
# 자주 쓰는 명령을 한 곳에 모아 둔 진입점입니다.
# 실행되는 실제 명령을 매번 출력하므로, 익숙해지면 그대로 직접 쓰셔도 됩니다.
#
#   ./scripts/dev.sh help
#   ./scripts/dev.sh up
#   ./scripts/dev.sh logs backend
#
set -euo pipefail

# 어디서 실행하든 저장소 루트를 기준으로 동작한다.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GPU_COMPOSE=(-f docker-compose.yml -f deploy/docker-compose.gpu.yml)

C_STEP=$'\033[36m'; C_DIM=$'\033[90m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_OFF=$'\033[0m'

step()  { printf '\n%s→ %s%s\n' "$C_STEP" "$1" "$C_OFF"; }
run()   { printf '%s  $ %s%s\n' "$C_DIM" "$*" "$C_OFF"; "$@"; }
# 비밀번호가 섞인 명령용 — 실행은 하되 화면에는 마스킹해서 보여 준다.
run_masked() { printf '%s  $ %s%s\n' "$C_DIM" "$1" "$C_OFF"; shift; "$@"; }
ok()    { printf '%s  %s%s\n' "$C_OK" "$1" "$C_OFF"; }
warn()  { printf '%s  %s%s\n' "$C_WARN" "$1" "$C_OFF"; }

require_env_file() {
  if [ ! -f .env ]; then
    warn ".env 파일이 없습니다. 템플릿을 복사합니다."
    cp .env.example .env
    warn ".env 를 열어 최소한 아래 값을 채운 뒤 다시 실행하세요:"
    echo "    NEO4J_PASSWORD=..."
    echo "    OPENAI_API_KEY=...   (RUNTIME_LLM=openai 로 쓸 때)"
    exit 1
  fi
}

require_backend_installed() {
  # backend/ 아래에서 `python -c "import yhs"` 가 되는지 본다.
  # 안 되면 editable 설치가 아직 안 된 것이다.
  if ! ( cd backend && python -c "import yhs" >/dev/null 2>&1 ); then
    warn "백엔드 패키지가 설치돼 있지 않습니다."
    echo "    먼저 실행하세요:  ./scripts/dev.sh install"
    echo "    (도커로만 쓸 거라면 이 명령 대신 ./scripts/dev.sh up 을 쓰세요)"
    exit 1
  fi
}

env_value() {
  [ -f .env ] || return 0
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" .env | head -1 | tr -d '\r'
}

show_help() {
  cat <<'EOF'

yhs 개발 명령
  사용법: ./scripts/dev.sh <명령>

  도커로 전체 실행
    up             스택 기동 (CPU torch) — 처음이라면 이것부터
    up-gpu         스택 기동 (CUDA torch + GPU 할당, NVIDIA 필요)
    down           스택 정지·정리
    restart        스택 재기동
    build          이미지만 빌드
    logs [서비스]  로그 추적 (기본: backend)
    ps             컨테이너 상태

  지식베이스
    ingest         data/sources 의 PDF 를 Neo4j 에 적재 (LLM 호출·비용 발생)
    migrate-kb     다른 Neo4j 의 그래프를 컨테이너로 복사 (LLM 미사용)
    kb-status      적재 상태 확인 (노드·청크 수)

  도커 없이 로컬 개발
    install        백엔드·프론트 의존성 설치
    backend        백엔드 개발 서버 (http://localhost:8000)
    frontend       프론트 개발 서버 (http://localhost:5173)
    cli            터미널 질의 루프

  품질
    test           백엔드 단위 테스트
    lint           파이썬 + 프론트 린트
    fmt            자동 수정 가능한 린트 문제 고치기
    clean          캐시·빌드 산출물 정리

  접속 주소
    프론트   http://localhost:3000
    API 문서 http://localhost:8000/docs
    Neo4j    http://localhost:7474

EOF
}

cmd="${1:-help}"
shift || true

case "$cmd" in

  help|-h|--help) show_help ;;

  up)
    require_env_file
    step "도커 스택 기동 (CPU torch)"
    run docker compose up -d --build
    ok "기동했습니다. 백엔드는 임베딩 모델을 올리느라 1~3분 걸립니다."
    echo "    상태 확인: ./scripts/dev.sh ps"
    echo "    로그 보기: ./scripts/dev.sh logs"
    echo "    프론트   : http://localhost:3000"
    ;;

  up-gpu)
    require_env_file
    step "도커 스택 기동 (CUDA torch + GPU)"
    printf '%s  GPU 가 도커에서 보이는지 먼저 확인하세요:\n    docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi%s\n' "$C_DIM" "$C_OFF"
    run docker compose "${GPU_COMPOSE[@]}" up -d --build
    ok "GPU 사용 여부는 백엔드 로그에서 확인합니다:"
    echo "    임베딩 모델 로드 완료: BAAI/bge-m3 (device=cuda:0)"
    ;;

  down)    step "도커 스택 정지"; run docker compose down ;;
  restart) step "도커 스택 재기동"; run docker compose restart ;;
  build)   step "이미지 빌드"; run docker compose build ;;
  ps)      run docker compose ps ;;

  logs)
    service="${1:-backend}"
    step "$service 로그 (Ctrl+C 로 종료)"
    run docker compose logs -f --tail 100 "$service"
    ;;

  ingest)
    step "지식베이스 구축 (data/sources → Neo4j)"
    warn "PDF 마다 LLM 을 부르므로 시간과 API 비용이 듭니다."
    run docker compose exec backend yhs --ingest
    ;;

  migrate-kb)
    step "다른 Neo4j 의 그래프를 컨테이너로 복사"
    pw="$(env_value NEO4J_PASSWORD)"
    [ -n "$pw" ] || { echo ".env 에 NEO4J_PASSWORD 가 없습니다." >&2; exit 1; }
    src="${1:-neo4j://host.docker.internal:7687}"
    printf '%s  원본: %s\n  대상: neo4j://neo4j:7687 (컨테이너)%s\n' "$C_DIM" "$src" "$C_OFF"
    docker compose exec -T \
      -e SRC_URI="$src" -e SRC_USER=neo4j -e SRC_PASSWORD="$pw" \
      -e DST_URI=neo4j://neo4j:7687 -e DST_USER=neo4j -e DST_PASSWORD="$pw" \
      -e PYTHONIOENCODING=utf-8 \
      backend python - < scripts/copy_graph.py
    ;;

  kb-status)
    step "지식베이스 적재 상태"
    pw="$(env_value NEO4J_PASSWORD)"
    [ -n "$pw" ] || { echo ".env 에 NEO4J_PASSWORD 가 없습니다." >&2; exit 1; }
    run_masked "docker compose exec -T neo4j cypher-shell -u neo4j -p ***** <cypher>" \
      docker compose exec -T neo4j cypher-shell -u neo4j -p "$pw" \
      "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC"
    ;;

  install)
    step "백엔드 의존성 설치"
    ( cd backend && run python -m pip install -e ".[dev]" && run python -m playwright install chromium )
    step "프론트 의존성 설치"
    ( cd frontend && run npm ci )
    ;;

  backend)
    require_backend_installed
    step "백엔드 개발 서버 (http://localhost:8000/docs)"
    ( cd backend && run python -m uvicorn yhs.api.main:app --reload )
    ;;

  frontend)
    step "프론트 개발 서버 (http://localhost:5173)"
    ( cd frontend && run npm run dev )
    ;;

  cli)
    require_backend_installed
    step "터미널 질의 루프"
    ( cd backend && run python -m yhs.cli --query )
    ;;

  test)
    step "백엔드 단위 테스트 (integration 제외)"
    ( cd backend && run python -m pytest -m "not integration" )
    ;;

  lint)
    step "파이썬 린트 (ruff)"
    run python -m ruff check .
    step "프론트 린트 (eslint)"
    ( cd frontend && run npm run lint )
    ;;

  fmt)
    step "자동 수정 (ruff --fix)"
    run python -m ruff check --fix .
    ;;

  clean)
    step "캐시·빌드 산출물 정리"
    rm -rf .cache .ruff_cache .pytest_cache backend/coverage.xml frontend/dist
    find . -name __pycache__ -type d -not -path './.venv/*' -not -path './frontend/node_modules/*' \
      -exec rm -rf {} + 2>/dev/null || true
    ok "정리 완료"
    ;;

  *)
    echo "알 수 없는 명령: $cmd" >&2
    show_help
    exit 1
    ;;
esac
