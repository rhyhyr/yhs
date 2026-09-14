export const calendarEvents = {
  '2026-08-10': [{ title: '비자 연장 서류 준비', color: '#5B45C2', type: '비자', desc: '만료 35일 전 — 서류 준비 권장' }],
  '2026-08-15': [{ title: 'D-2 비자 만료일', color: '#D13B3B', type: '비자', desc: '이 날 이전에 연장 완료 필수' }],
  '2026-08-20': [{ title: '건강보험료 납부', color: '#1A8C5B', type: '보험', desc: '8월분 납부 마감' }],
  '2026-08-25': [{ title: '수강신청 정정기간', color: '#2155CD', type: '학교', desc: '학교 포털에서 정정 가능' }],
};

export const INITIAL_STEPS = [
  { id: 1, text: '여권 원본 + 사본 1부', sub: '유효기간 6개월 이상', checked: true, current: false },
  { id: 2, text: '외국인등록증 원본', sub: '', checked: true, current: false },
  { id: 3, text: '재학증명서 (영문) 발급', sub: '포털 → 증명서 발급 → 영문 재학증명서', checked: false, current: true },
  { id: 4, text: '수수료 60,000원 준비', sub: '', checked: false, current: false },
  { id: 5, text: '출입국관리사무소 방문 예약', sub: 'Hi Korea에서 사전 예약 필수', checked: false, current: false },
  { id: 6, text: '방문 접수 및 수령', sub: '처리 기간 약 5~7 영업일', checked: false, current: false },
];

export function formatDateKey(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
