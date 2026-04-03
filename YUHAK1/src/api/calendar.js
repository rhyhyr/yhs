/**
 * src/api/calendar.js
 * ─────────────────────────────────────────────
 * 캘린더 이벤트 API 레이어
 *
 * 현재: mock 데이터 반환 (개발 단계)
 * 이후: 주석 처리된 fetch 블록으로 교체하면 됩니다.
 *
 * ── 백엔드 계약 (예상 엔드포인트) ──────────────────
 *
 * [getCalendarEvents]
 * GET /api/calendar?year=2026&month=8
 * Response:
 *   {
 *     "events": {
 *       "2026-08-10": [{ "title": "비자 연장 서류 준비", "color": "#5B45C2", "type": "비자", "desc": "..." }],
 *       "2026-08-15": [{ "title": "D-2 비자 만료일", "color": "#D13B3B", "type": "비자", "desc": "..." }]
 *     }
 *   }
 */

import { BASE_URL } from './config';
import { calendarEvents } from './mockData';

// ── API 함수 ─────────────────────────────────────────────────────────────

/**
 * 특정 년·월의 캘린더 이벤트 조회
 *
 * @param {number} year   — 4자리 연도 (예: 2026)
 * @param {number} month  — 0-indexed 월 (예: 7 = 8월)
 * @returns {Promise<Record<string, Array<{ title, color, type, desc }>>>}
 *          키: "YYYY-MM-DD", 값: 해당 날짜 이벤트 배열
 */
export async function getCalendarEvents(year, month) {
  // ── mock: mockData에서 해당 년·월 이벤트 필터링
  const prefix = `${year}-${String(month + 1).padStart(2, '0')}`;
  const filtered = {};
  Object.entries(calendarEvents).forEach(([key, val]) => {
    if (key.startsWith(prefix)) filtered[key] = val;
  });
  return filtered;

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(
    `${BASE_URL}/api/calendar?year=${year}&month=${month + 1}`,
    { headers: authHeader() }
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.events ?? {};
  */
}

// ── 내부 유틸 ─────────────────────────────────────────────────────────────

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
