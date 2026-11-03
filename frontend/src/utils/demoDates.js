/**
 * src/utils/demoDates.js
 * ─────────────────────────────────────────────
 * 시연용 mock 날짜를 "오늘 기준"으로 만든다.
 * 날짜를 '2026-08-15'처럼 박아 두면 시간이 지나 이미 지난 날짜가 화면에 나오므로,
 * 비자 만료일 = 오늘 + 87일(D-87)을 기준으로 체크리스트 마감일 등을 상대적으로 계산한다.
 * (백엔드에서 실제 값을 받게 되면 이 파일은 필요 없어진다)
 */

/** 시연용 비자 만료까지 남은 날 */
export const DEMO_VISA_DDAY = 87;

/** 오늘 + days 일 → 'YYYY-MM-DD' (로컬 시간 기준) */
export function fromToday(days) {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + days);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mm}-${dd}`;
}

/** 'YYYY-MM-DD' → 'YYYY. M. D' */
export function dotLabel(ymd) {
  const [y, m, d] = ymd.split('-').map(Number);
  return `${y}. ${m}. ${d}`;
}
