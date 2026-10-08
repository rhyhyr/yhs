/**
 * src/utils/googleCalendar.js
 * ─────────────────────────────────────────────
 * 구글 캘린더 연동 — 로그인 없이 되는 방식만 구현.
 *
 *   1. buildGoogleCalendarUrl  — 일정 하나를 구글 캘린더 "추가" 화면
 *      URL로 변환 (새 탭으로 열면 제목·날짜가 미리 채워진 채로 뜸)
 *   2. buildIcsFile            — 여러 일정을 표준 .ics 파일 내용으로 변환
 *      (구글 캘린더 "가져오기"로 한 번에 넣을 수 있음, 다른 캘린더 앱도 호환)
 *   3. downloadIcsFile         — 2번 결과를 실제 파일 다운로드로 트리거
 *
 * 전부 로그인·백엔드 없이 프론트엔드만으로 동작한다.
 */

/** 'YYYY-MM-DD' → 다음 날 'YYYY-MM-DD' (구글 캘린더는 종일 일정의 종료일을 배타적으로 씀) */
function nextDay(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d + 1);
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
}

/** 'YYYY-MM-DD' → 'YYYYMMDD' */
function compact(dateStr) {
  return dateStr.replace(/-/g, '');
}

/**
 * 일정 하나를 구글 캘린더 "빠른 추가" 화면 URL로 변환.
 * @param {{ title: string, description?: string, dateStr: string }} event
 * @returns {string}
 */
export function buildGoogleCalendarUrl({ title, description, dateStr }) {
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: title,
    dates: `${compact(dateStr)}/${compact(nextDay(dateStr))}`,
  });
  if (description) params.set('details', description);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

/** .ics TEXT 값 이스케이프 (RFC 5545) — 콤마·세미콜론·백슬래시·줄바꿈 처리 */
function escapeIcsText(text) {
  return String(text)
    .replace(/\\/g, '\\\\')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;')
    .replace(/\r?\n/g, '\\n');
}

/** DTSTAMP(파일 생성 시각)용 — UTC 기준 'YYYYMMDDTHHMMSSZ' */
function nowStamp() {
  return new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
}

/**
 * 여러 일정을 하나의 .ics 캘린더 파일 내용으로 변환.
 * @param {Array<{ uid: string, title: string, description?: string, dateStr: string }>} events
 * @returns {string} .ics 파일 전체 내용 (CRLF 줄바꿈)
 */
export function buildIcsFile(events) {
  const stamp = nowStamp();
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//YuGuide//Checklist//KO', 'CALSCALE:GREGORIAN'];

  events.forEach(({ uid, title, description, dateStr }) => {
    lines.push(
      'BEGIN:VEVENT',
      `UID:${uid}@yuguide`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${compact(dateStr)}`,
      `DTEND;VALUE=DATE:${compact(nextDay(dateStr))}`,
      `SUMMARY:${escapeIcsText(title)}`,
    );
    if (description) lines.push(`DESCRIPTION:${escapeIcsText(description)}`);
    lines.push('END:VEVENT');
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

/**
 * .ics 파일을 실제로 다운로드 트리거 (브라우저 전용 — DOM 필요).
 * @param {string} filename
 * @param {Array} events — buildIcsFile과 동일한 형식
 */
export function downloadIcsFile(filename, events) {
  const content = buildIcsFile(events);
  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename.endsWith('.ics') ? filename : `${filename}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
