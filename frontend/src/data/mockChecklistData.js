/**
 * src/data/mockChecklistData.js
 * ─────────────────────────────────────────────
 * 채팅 체크리스트 mock 데이터
 *
 * 실제 서비스에서는 AI 응답 파싱 또는 API 응답으로 교체합니다.
 * 이 파일만 교체(또는 API 레이어로 래핑)하면 실제 데이터로 전환됩니다.
 *
 * ── 타입 정의 ──────────────────────────────────────────────
 *
 * ChecklistItem:
 * {
 *   id      : number    — 항목 고유 ID
 *   text    : string    — 항목 이름
 *   sub     : string    — 보조 설명 (없으면 '')
 *   dueDate : string    — 마감일 'YYYY-MM-DD'
 * }
 *
 * ChatChecklist:
 * {
 *   id    : string           — 체크리스트 고유 ID
 *   title : string           — 표시 제목
 *   type  : string           — 캘린더 이벤트 타입 레이블
 *   color : string           — 이벤트 색상 hex
 *   items : ChecklistItem[]
 * }
 */

/** @type {Record<string, import('./mockChecklistData').ChatChecklist>} */
export const MOCK_CHECKLISTS = {
  'arc-renew': {
    id:    'arc-renew',
    title: '외국인등록증 재발급',
    type:  'ARC 재발급',
    color: '#D13B3B',
    items: [
      { id: 1, text: '여권 원본',            sub: '유효기간 남아 있는지 확인',               dueDate: '2026-07-03' },
      { id: 2, text: '사진 1장',             sub: '여권용 사진 3.5 × 4.5cm',                dueDate: '2026-07-03' },
      { id: 3, text: '재발급 신청서',         sub: '출입국관리사무소 비치 또는 Hi Korea 출력', dueDate: '2026-07-05' },
      { id: 4, text: '수수료 30,000원',       sub: '현금 또는 카드 준비',                     dueDate: '2026-07-05' },
      { id: 5, text: 'Hi Korea 방문 예약',    sub: 'www.hikorea.go.kr — 예약 필수',           dueDate: '2026-07-08' },
      { id: 6, text: '출입국관리사무소 방문',  sub: '예약 날짜에 서류 지참 방문',               dueDate: '2026-07-10' },
      { id: 7, text: '새 외국인등록증 수령',   sub: '처리 기간 약 3~5 영업일',                 dueDate: '2026-07-15' },
    ],
  },

  'visa-extension': {
    id:    'visa-extension',
    title: '비자 연장',
    type:  '비자 연장',
    color: '#5B45C2',
    items: [
      { id: 1, text: '여권 원본 + 사본 1부',      sub: '유효기간 6개월 이상',                dueDate: '2026-08-01' },
      { id: 2, text: '외국인등록증 원본',          sub: '',                                  dueDate: '2026-08-01' },
      { id: 3, text: '재학증명서 (영문) 발급',     sub: '포털 → 증명서 발급 → 영문 재학증명서', dueDate: '2026-08-05' },
      { id: 4, text: '수수료 60,000원 준비',       sub: '',                                  dueDate: '2026-08-08' },
      { id: 5, text: '출입국관리사무소 방문 예약', sub: 'Hi Korea에서 사전 예약 필수',          dueDate: '2026-08-10' },
      { id: 6, text: '방문 접수 및 수령',          sub: '처리 기간 약 5~7 영업일',             dueDate: '2026-08-15' },
    ],
  },

  'school-registration': {
    id:    'school-registration',
    title: '수강신청 준비',
    type:  '수강신청',
    color: '#2155CD',
    items: [
      { id: 1, text: '학사일정 확인',           sub: '포털 → 학사일정 → 등록금 납부·수강신청 기간', dueDate: '2026-08-20' },
      { id: 2, text: '등록금 고지서 확인',       sub: '포털 로그인 → 등록금 고지 메뉴',             dueDate: '2026-08-22' },
      { id: 3, text: '등록금 납부',              sub: '납부 기간 내 은행 이체 또는 포털 결제',       dueDate: '2026-08-24' },
      { id: 4, text: '수강신청 날짜·시간 확인',  sub: '학년·학과별 신청 시작 시간이 다를 수 있음',   dueDate: '2026-08-25' },
      { id: 5, text: '시간표 미리 계획',          sub: '전공/교양 이수 조건 함께 확인',               dueDate: '2026-08-26' },
      { id: 6, text: '수강신청 완료',            sub: '학교 포털에서 희망 과목 신청',                 dueDate: '2026-08-28' },
      { id: 7, text: '수강 결과 확인',           sub: '신청 결과 조회 후 수강정정 기간에 변경 가능',   dueDate: '2026-08-30' },
    ],
  },
};

/**
 * 체크리스트 ID로 단건 조회
 * @param {string} id
 * @returns {ChatChecklist|null}
 */
export function getMockChecklist(id) {
  return MOCK_CHECKLISTS[id] ?? null;
}

/** checklistId → 이동할 화면 ID */
export const CHECKLIST_SCREEN = {
  'arc-renew':           's-arc-checklist',
  'visa-extension':      's-step',
  'school-registration': 's-school-checklist',
};
