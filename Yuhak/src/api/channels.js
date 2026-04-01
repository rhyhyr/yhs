/**
 * 채널 레지스트리 — 단일 소스
 *
 * 새 채널 추가 시 여기만 수정.
 * ChannelChatScreen, 래퍼 화면, HomeScreen 모두 이 파일을 참조.
 */
export const CHANNELS = {
  visa: {
    id: 'visa',
    name: '비자 & 체류',
    icon: '🛂',
    iconBg: 'var(--c-purple-l)',
    screenId: 's-visa',
    welcomeMsg: 'D-2 채널입니다. 만료까지 87일 남았어요. 비자 관련 무엇이든 질문해주세요!',
    placeholder: '비자 관련 질문하기...',
  },
  school: {
    id: 'school',
    name: '학교생활',
    icon: '🏫',
    iconBg: 'var(--c-green-l)',
    screenId: 's-school',
    welcomeMsg: '학교생활 채널입니다. 수강신청, 학사 일정, 장학금, 기숙사 등 학교 관련 질문을 해주세요!',
    placeholder: '학교생활 관련 질문하기...',
  },
  job: {
    id: 'job',
    name: '취업 & 아르바이트',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    screenId: 's-job',
    welcomeMsg: '취업 & 아르바이트 채널입니다. 시간제 취업 허가, 아르바이트 규정, 인턴십 관련 질문을 해주세요!',
    placeholder: '취업 · 아르바이트 관련 질문하기...',
  },
  house: {
    id: 'house',
    name: '주거',
    icon: '🏠',
    iconBg: 'var(--c-accent-l)',
    screenId: 's-house',
    welcomeMsg: '주거 채널입니다. 전월세 계약, 관리비, 이사, 외국인 임대차 주의사항 등 주거 관련 질문을 해주세요!',
    placeholder: '주거 관련 질문하기...',
  },
  insurance: {
    id: 'insurance',
    name: '병원 & 보험',
    icon: '🏥',
    iconBg: '#FEE2E2',
    screenId: 's-insurance',
    welcomeMsg: '병원 & 보험 채널입니다. 건강보험 가입, 병원 이용 방법, 보험 혜택 등을 안내해 드립니다!',
    placeholder: '병원 · 보험 관련 질문하기...',
  },
  main: {
    id: 'main',
    name: '메인 채팅',
    icon: '💬',
    iconBg: 'var(--c-accent-l)',
    screenId: 's-main',
    welcomeMsg: '안녕하세요! 무엇이든 질문하세요. 적합한 채널로 안내해 드리겠습니다.',
    placeholder: '무엇이든 질문하세요...',
  },
};

/** channelId로 채널 설정 조회 */
export function getChannel(id) {
  return CHANNELS[id] ?? null;
}
