/**
 * src/api/userProfile.js
 * ─────────────────────────────────────────────
 * 유저 프로필 서비스 레이어 — API 전환 포인트
 *
 * 현재: localStorage 사용
 * 이후: persistUserProfile / getUserProfile 내부만 fetch 호출로 교체하면 됩니다.
 *
 * ── 백엔드 계약 (예상 엔드포인트) ──────────────────
 * GET  /api/user/profile        → userProfile 객체 반환
 * PUT  /api/user/profile        → 저장 후 userProfile 반환
 */

import { saveUserProfileLocal, loadUserProfile } from '../utils/storage';

/**
 * 프로필 불러오기 (앱 시작 시 1회 호출)
 * @returns {Promise<object|null>}
 */
export async function getUserProfile() {
  // ── 현재: localStorage
  return loadUserProfile();

  /* ── API 전환 예시 (위 줄 삭제 후 아래 주석 해제)
  const res = await fetch('/api/user/profile', { headers: authHeader() });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

/**
 * 프로필 저장/덮어쓰기 (온보딩 완료, 정보 수정 시 호출)
 * @param {object} profile
 * @returns {Promise<object>} 저장된 profile
 */
export async function persistUserProfile(profile) {
  // ── 현재: localStorage
  saveUserProfileLocal(profile);
  return profile;

  /* ── API 전환 예시 (위 두 줄 삭제 후 아래 주석 해제)
  const res = await fetch('/api/user/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
