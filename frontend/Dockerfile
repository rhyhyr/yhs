# ─────────────────────────────────────────────────────────────────────────────
# yhs 프론트엔드 — React(Vite) → nginx 정적 서빙 + /api 리버스 프록시
# ─────────────────────────────────────────────────────────────────────────────

# ── 1단계: 빌드 ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# 잠금파일 기준 설치 → 재현 가능한 빌드. 소스보다 먼저 복사해 캐시를 살린다.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# 비워 두면 프론트가 같은 오리진(/api/...)으로 호출하고 nginx 가 프록시한다.
# 백엔드를 다른 도메인에 두는 경우에만 값을 준다.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 구글 캘린더 연동용 OAuth 클라이언트 ID. Vite 환경변수는 빌드 시점에 결과물에
# 박히므로(런타임에 못 바꿈) 반드시 이 빌드 단계에서 넘겨줘야 한다.
# 비워 두면(기본값) 구글 캘린더 연동 버튼이 "아직 설정 안 됨"으로 비활성 표시됨 —
# 빌드가 깨지진 않으니 값을 안 줘도 나머지 기능은 정상 동작한다.
ARG VITE_GOOGLE_CLIENT_ID=""
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

RUN npm run build


# ── 2단계: 서빙 ───────────────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  # localhost 가 아니라 127.0.0.1 을 쓴다. 컨테이너의 localhost 는 ::1 로도
  # 해석되는데 nginx 는 0.0.0.0:80(IPv4)에만 바인딩하므로, busybox wget 이
  # IPv6 를 먼저 시도해 Connection refused 로 떨어진다.
  CMD wget -q --spider http://127.0.0.1/ || exit 1
