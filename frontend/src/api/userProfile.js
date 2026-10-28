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
  const local = loadUserProfile();
  try {
    const res = await fetch('/api/user/profile', { headers: { 'X-Client-Id': getClientId() } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const remote = await res.json();
    if (Object.keys(remote).length) {
      saveUserProfileLocal(remote); // 다른 기기에서 저장한 값을 이 기기에도 반영
      return remote;
    }
  } catch (err) {
    console.warn('프로필 서버 조회 실패, 로컬 값을 사용합니다:', err);
    return local;
  }
  // 서버에 아직 없으면 이 기기의 로컬 프로필을 올려 둔다
  if (local) await persistUserProfile(local);
  return local;

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
  // 로컬에 먼저 저장하고, 서버 저장은 실패해도 앱을 막지 않는다.
  saveUserProfileLocal(profile);
  try {
    const res = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Client-Id': getClientId() },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    console.warn('프로필 서버 저장 실패 (로컬에는 저장됨):', err);
  }
  return profile;

  /* ── 이전 주석 (참고용)
  const res = await fetch('/api/user/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

// 브라우저마다 한 번 만들어 두는 ID — 인증 전까지 프로필을 기기별로 나누는 키
const CLIENT_ID_KEY = 'yhs_client_id';

function getClientId() {
  let id = localStorage.getItem(CLIENT_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(CLIENT_ID_KEY, id);
  }
  return id;
}

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
