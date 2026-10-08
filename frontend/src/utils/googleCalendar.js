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
 *   4. createGoogleCalendarEvent(s) — (구글 연결된 경우) 진짜로 Calendar API를
 *      호출해서 사용자 캘린더에 바로 등록. googleAuth.js에서 받은 접근 토큰 필요.
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

/**
 * 구글 연결(접근 토큰)이 돼 있을 때, 일정 하나를 진짜로 사용자의
 * 기본 캘린더에 추가한다 (Calendar API 직접 호출, 백엔드 안 거침).
 *
 * @param {string} accessToken
 * @param {{ title: string, description?: string, dateStr: string }} event
 * @throws {Error} 토큰 만료(401) 등 API 에러 시 — 메시지에 상태 코드 포함
 */
export async function createGoogleCalendarEvent(accessToken, { title, description, dateStr }) {
  const res = await fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      summary: title,
      description: description || undefined,
      start: { date: dateStr },
      end: { date: nextDay(dateStr) },
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const err = new Error(body?.error?.message || `Google Calendar API 오류 (HTTP ${res.status})`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

/**
 * 여러 일정을 순서대로 등록 (Calendar API는 REST 엔드포인트상 한 번에
 * 여러 개를 넣는 기능이 없어서 하나씩 보낸다 — 체크리스트 규모(수 개~십여 개)엔 충분).
 * @returns {Promise<{ succeeded: number, failed: number, authExpired: boolean }>}
 *   authExpired: 실패 중 하나라도 401(토큰 만료)이었는지 — 재연결 유도 여부 판단용
 */
export async function createGoogleCalendarEvents(accessToken, events) {
  let succeeded = 0;
  let failed = 0;
  let authExpired = false;
  for (const event of events) {
    if (authExpired) { failed += 1; continue; } // 토큰이 만료된 걸 확인했으면 나머지는 호출 자체를 건너뜀
    try {
      await createGoogleCalendarEvent(accessToken, event);
      succeeded += 1;
    } catch (err) {
      failed += 1;
      if (err.status === 401) authExpired = true;
    }
  }
  return { succeeded, failed, authExpired };
}
