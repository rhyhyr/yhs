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
RUN npm run build


# ── 2단계: 서빙 ───────────────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://localhost/ || exit 1
