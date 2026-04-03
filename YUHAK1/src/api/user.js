/**
 * src/api/user.js
 * ─────────────────────────────────────────────
 * 사용자 프로필 · 비자 정보 API 레이어
 *
 * 현재: mock 데이터 반환 (개발 단계)
 * 이후: 주석 처리된 fetch 블록으로 교체하면 됩니다.
 *
 * ── 백엔드 계약 (예상 엔드포인트) ──────────────────
 *
 * [getMyProfile]
 * GET /api/user/me
 * Response: { name, initial, school, department, grade, nationality, nationalityFlag }
 *
 * [getVisaInfo]
 * GET /api/user/visa
 * Response: { type, label, expiryDate, expiryLabel, dDay }
 *
 * [getMyChannels]
 * GET /api/user/channels
 * Response: { channels: [{ id, label, channelId, iconBg }] }
 *
 * [createChannel]
 * POST /api/user/channels
 * Request:  { channelId }
 * Response: { ok, channelId }
 */

import { BASE_URL } from './config';

// ── Mock 데이터 ───────────────────────────────────────────────────────────

const MOCK_PROFILE = {
  name: 'Wei Zhang',
  initial: 'W',
  school: '동아대학교',
  department: 'AI학과',
  grade: 4,
  nationality: '중국',
  nationalityFlag: '🇨🇳',
};

const MOCK_VISA = {
  type: 'D-2',
  label: 'D-2 (학생)',
  expiryDate: '2026-08-15',
  expiryLabel: '2026. 8. 15',
  dDay: 87,
};

// ── API 함수 ─────────────────────────────────────────────────────────────

/**
 * 내 프로필 정보 조회
 * @returns {Promise<{ name, initial, school, department, grade, nationality, nationalityFlag }>}
 */
export async function getMyProfile() {
  // ── mock 반환
  return MOCK_PROFILE;

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/user/me`, { headers: authHeader() });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

/**
 * 내 비자 정보 조회
 * @returns {Promise<{ type, label, expiryDate, expiryLabel, dDay }>}
 */
export async function getVisaInfo() {
  // ── mock 반환
  return MOCK_VISA;

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/user/visa`, { headers: authHeader() });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

/**
 * 내가 생성한 채널 목록 조회
 * @returns {Promise<Array<{ id, label, channelId, iconBg }>>}
 */
export async function getMyChannels() {
  // ── mock: 빈 배열 반환 (로컬 상태로 관리)
  return [];

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/user/channels`, { headers: authHeader() });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.channels ?? [];
  */
}

/**
 * 채널 생성
 * @param {{ id, label, channelId, iconBg }} channel
 * @returns {Promise<{ ok: boolean, channelId: string }>}
 */
export async function createChannel(channel) {
  // ── mock: 성공 반환 (로컬 상태로만 관리)
  return { ok: true, channelId: channel.channelId ?? channel.id };

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/user/channels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ channelId: channel.channelId ?? channel.id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

// ── 내부 유틸 ─────────────────────────────────────────────────────────────

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
