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

// ── 체크리스트 → 캘린더 이벤트 변환 ──────────────────────────────────────

/**
 * 체크리스트 스텝 배열을 캘린더 이벤트 맵으로 변환
 *
 * @param {Array<{ steps, type, color }>} checklists
 *   - steps: 체크리스트 스텝 배열 (dueDate 필드가 있는 항목만 처리)
 *   - type:  표시할 타입 레이블 (예: '비자', 'ARC', '학교')
 *   - color: 이벤트 색상 hex (예: '#5B45C2')
 * @returns {Record<string, Array>}  키: "YYYY-MM-DD", 값: 이벤트 배열
 */
export function checklistsToEvents(checklists) {
  const result = {};
  checklists.forEach(({ steps, type, color }) => {
    steps.forEach(step => {
      if (!step.dueDate) return;
      if (!result[step.dueDate]) result[step.dueDate] = [];
      result[step.dueDate].push({
        title: step.text,
        desc: step.sub || null,
        color,
        type,
        source: 'checklist',
        checklistItemId: step.id,
        isCompleted: step.checked,
      });
    });
  });
  return result;
}

/**
 * 여러 이벤트 맵을 날짜 키 기준으로 병합
 * 같은 날짜에 여러 출처의 이벤트가 있으면 배열로 합쳐짐
 */
export function mergeEvents(...eventMaps) {
  const result = {};
  eventMaps.forEach(map => {
    Object.entries(map).forEach(([date, evts]) => {
      result[date] = [...(result[date] ?? []), ...evts];
    });
  });
  return result;
}

/**
 * 채팅 체크리스트에서 선택된 항목만 캘린더 이벤트 맵으로 변환
 *
 * @param {import('../data/mockChecklistData').ChatChecklist} checklist
 * @param {number[]} selectedItemIds  — 사용자가 선택한 item.id 배열
 * @returns {Record<string, Array>}
 */
export function convertChecklistItemsToEvents(checklist, selectedItemIds) {
  const selectedSet = new Set(selectedItemIds);
  const result      = {};

  checklist.items
    .filter(item => selectedSet.has(item.id) && item.dueDate)
    .forEach(item => {
      if (!result[item.dueDate]) result[item.dueDate] = [];
      result[item.dueDate].push({
        title:           item.text,
        desc:            item.sub || null,
        color:           checklist.color,
        type:            checklist.type,
        source:          'chat-checklist',
        checklistId:     checklist.id,
        checklistItemId: item.id,
        isCompleted:     false,
      });
    });

  return result;
}

// ── 내부 유틸 ─────────────────────────────────────────────────────────────

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
