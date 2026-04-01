/**
 * API 설정 — 환경변수 단일 진입점
 *
 * 모든 API 호출은 여기서 BASE_URL을 참조합니다.
 * 실제 fetch 추가 시: fetch(`${BASE_URL}/endpoint`)
 */
export const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
export const APP_NAME = import.meta.env.VITE_APP_NAME ?? 'UniGuide AI';
