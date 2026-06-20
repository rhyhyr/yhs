// 캘린더 목데이터 제거 — 채팅으로 추가된 항목만 표시
export const calendarEvents = {};

export const ARC_RENEW_STEPS = [
  { id: 1, text: '여권 원본',                  sub: '유효기간 남아 있는지 확인',              checked: false, current: true,  dueDate: '2026-07-03' },
  { id: 2, text: '사진 1장',                   sub: '여권용 사진 3.5 × 4.5cm',               checked: false, current: false, dueDate: '2026-07-03' },
  { id: 3, text: '재발급 신청서',               sub: '출입국관리사무소 비치 또는 Hi Korea 출력', checked: false, current: false, dueDate: '2026-07-05' },
  { id: 4, text: '수수료 30,000원',             sub: '현금 또는 카드 준비',                    checked: false, current: false, dueDate: '2026-07-05' },
  { id: 5, text: 'Hi Korea 방문 예약',          sub: 'www.hikorea.go.kr — 예약 필수',          checked: false, current: false, dueDate: '2026-07-08' },
  { id: 6, text: '출입국관리사무소 방문',        sub: '예약 날짜에 서류 지참 방문',              checked: false, current: false, dueDate: '2026-07-10' },
  { id: 7, text: '새 외국인등록증 수령',         sub: '처리 기간 약 3~5 영업일',                checked: false, current: false, dueDate: '2026-07-15' },
];

export const SCHOOL_REGISTER_STEPS = [
  { id: 1, text: '학사일정 확인',           sub: '학교 포털 → 학사일정 → 등록금 납부·수강신청 기간 확인', checked: false, current: true,  dueDate: '2026-08-20' },
  { id: 2, text: '등록금 고지서 확인',      sub: '포털 로그인 → 등록금 고지 메뉴',                        checked: false, current: false, dueDate: '2026-08-22' },
  { id: 3, text: '등록금 납부',             sub: '납부 기간 내 은행 이체 또는 포털 결제',                  checked: false, current: false, dueDate: '2026-08-24' },
  { id: 4, text: '수강신청 날짜·시간 확인', sub: '학년·학과별 신청 시작 시간이 다를 수 있음',               checked: false, current: false, dueDate: '2026-08-25' },
  { id: 5, text: '시간표 미리 계획',         sub: '전공/교양 이수 조건 함께 확인',                          checked: false, current: false, dueDate: '2026-08-26' },
  { id: 6, text: '수강신청 완료',           sub: '학교 포털에서 희망 과목 신청',                            checked: false, current: false, dueDate: '2026-08-28' },
  { id: 7, text: '수강 결과 확인',          sub: '신청 결과 조회 후 수강정정 기간에 변경 가능',               checked: false, current: false, dueDate: '2026-08-30' },
];

export const INITIAL_STEPS = [
  { id: 1, text: '여권 원본 + 사본 1부', sub: '유효기간 6개월 이상',                       checked: true,  current: false, dueDate: '2026-08-01' },
  { id: 2, text: '외국인등록증 원본',     sub: '',                                         checked: true,  current: false, dueDate: '2026-08-01' },
  { id: 3, text: '재학증명서 (영문) 발급', sub: '포털 → 증명서 발급 → 영문 재학증명서',    checked: false, current: true,  dueDate: '2026-08-05' },
  { id: 4, text: '수수료 60,000원 준비',  sub: '',                                         checked: false, current: false, dueDate: '2026-08-08' },
  { id: 5, text: '출입국관리사무소 방문 예약', sub: 'Hi Korea에서 사전 예약 필수',          checked: false, current: false, dueDate: '2026-08-10' },
  { id: 6, text: '방문 접수 및 수령',     sub: '처리 기간 약 5~7 영업일',                  checked: false, current: false, dueDate: '2026-08-15' },
];

export function formatDateKey(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
