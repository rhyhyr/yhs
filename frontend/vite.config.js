import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const appName = env.VITE_APP_NAME || 'YuGuide AI'

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        // 개발 서버에서도 서비스워커를 등록해서 로컬에서 설치·오프라인 동작을 바로 확인할 수 있게 함
        devOptions: { enabled: true, type: 'module' },
        manifest: {
          name: appName,
          short_name: 'YuGuide',
          description: '유학생을 위한 비자·학교·생활 안내 AI 어시스턴트',
          lang: 'ko',
          start_url: '/',
          display: 'standalone',
          background_color: '#F5F4F0', // --c-bg — 스플래시 배경과 맞춤
          theme_color: '#2155CD',      // --c-accent
          icons: [
            { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
            // maskable: 안드로이드가 아이콘을 원형 등으로 잘라도 로고가 안 잘리게 여백을 더 준 버전
            { src: '/icons/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
          ],
        },
        workbox: {
          // 이 앱은 라우터 없이 SPA 하나로 동작하므로 모든 경로를 index.html 로 폴백
          navigateFallback: '/index.html',
          // /api/* 는 캐시하지 않음 — 채팅·프로필 등은 항상 최신 응답이어야 함
          navigateFallbackDenylist: [/^\/api\//],
        },
      }),
    ],
    server: {
      // 개발 중에도 프론트는 같은 오리진의 /api/... 로 호출한다.
      // 운영에서 nginx 가 하는 일을 dev 서버가 대신 해 주므로
      // 코드에 백엔드 주소를 넣을 필요가 없고 CORS 도 걸리지 않는다.
      proxy: {
        '/api': {
          target: env.VITE_DEV_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
      // Vite 는 기본적으로 모르는 Host 헤더의 요청을 403으로 막는다(DNS 리바인딩 방지).
      // cloudflared 임시 터널(폰 실기기 테스트용)로 들어오는 요청만 예외로 허용.
      // 운영 빌드(nginx)에는 영향 없음 — 개발 서버 전용 설정.
      allowedHosts: ['.trycloudflare.com'],
    },
  }
})
