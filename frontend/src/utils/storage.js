/**
 * src/utils/storage.js
 * ─────────────────────────────────────────────
 * localStorage 로우레벨 유틸 — 이 파일은 직접 호출하지 말고
 * userProfileService.js 를 통해 사용하세요.
 */

const PROFILE_KEY = 'userProfile';

/** localStorage에 프로필 저장 */
export function saveUserProfileLocal(profile) {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

/** localStorage에서 프로필 불러오기. 없거나 파싱 실패 시 null */
export function loadUserProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
