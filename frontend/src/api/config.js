/**
 * API 설정 — 환경변수 단일 진입점
 *
 * 모든 API 호출은 여기서 BASE_URL 을 참조합니다.
 *
 * 기본값이 빈 문자열인 이유:
 *   같은 오리진의 `/api/...` 로 호출하면
 *     - 개발:  vite dev 서버가 프록시 (vite.config.js)
 *     - 운영:  nginx 가 프록시 (frontend/nginx.conf)
 *   둘 다 알아서 백엔드로 넘겨 줍니다. 주소를 코드에 박을 필요가 없고
 *   CORS 설정도 필요 없습니다.
 *
 * 백엔드를 다른 도메인에 두는 경우에만 VITE_API_BASE_URL 을 설정하세요.
 */
export const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
export const APP_NAME = import.meta.env.VITE_APP_NAME ?? 'UniGuide AI';

/** true 면 백엔드를 호출하지 않고 mock 데이터만 씁니다 (디자인 작업용). */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
