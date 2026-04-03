/**
 * src/api/steps.js
 * ─────────────────────────────────────────────
 * 비자 체크리스트(단계) API 레이어
 *
 * 현재: mock 데이터 반환 (개발 단계)
 * 이후: 주석 처리된 fetch 블록으로 교체하면 됩니다.
 *
 * ── 백엔드 계약 (예상 엔드포인트) ──────────────────
 *
 * [getVisaSteps]
 * GET /api/visa/steps
 * Response:
 *   {
 *     "steps": [
 *       { "id": 1, "text": "여권 원본 + 사본 1부", "sub": "유효기간 6개월 이상", "checked": false, "current": true },
 *       ...
 *     ]
 *   }
 *
 * [updateStepStatus]
 * PATCH /api/visa/steps/:stepId
 * Request:  { "checked": true }
 * Response: { "ok": true }
 */

import { BASE_URL } from './config';
import { INITIAL_STEPS } from './mockData';

// ── API 함수 ─────────────────────────────────────────────────────────────

/**
 * 비자 연장 체크리스트 단계 조회
 * @returns {Promise<Array<{ id, text, sub, checked, current }>>}
 */
export async function getVisaSteps() {
  // ── mock: INITIAL_STEPS 반환
  return INITIAL_STEPS;

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/visa/steps`, { headers: authHeader() });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.steps ?? [];
  */
}

/**
 * 단계 체크 상태 저장
 * @param {number} stepId
 * @param {boolean} checked
 * @returns {Promise<{ ok: boolean }>}
 */
export async function updateStepStatus(stepId, checked) {
  // ── mock: no-op (로컬 상태로만 관리)
  return { ok: true };

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/visa/steps/${stepId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ checked }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
  */
}

// ── 내부 유틸 ─────────────────────────────────────────────────────────────

// function authHeader() {
//   return { Authorization: `Bearer ${localStorage.getItem('token')}` };
// }
