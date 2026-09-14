import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
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
    },
  }
})
