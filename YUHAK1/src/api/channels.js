/**
 * 채널 레지스트리 — 단일 소스
 *
 * 새 채널 추가 시 여기만 수정.
 * ChannelChatScreen, App.jsx, HomeScreen 모두 이 파일을 참조.
 *
 * quickActions: 채널 상단에 표시할 빠른 실행 버튼 (선택 사항)
 *   - type 'navigate': 다른 화면으로 이동
 *   - type 'question': 해당 텍스트를 채팅으로 전송
 */
export const CHANNELS = {
  visa: {
    id: 'visa',
    name: '비자 & 체류',
    icon: '🛂',
    iconBg: 'var(--c-purple-l)',
    welcomeMsg: 'D-2 채널입니다. 만료까지 87일 남았어요. 위 버튼을 탭하거나 직접 질문해주세요!',
    placeholder: '비자 관련 질문하기...',
    quickActions: [
      { label: '📋 비자 연장 절차', type: 'navigate', target: 's-step' },
      { label: '🪪 외국인등록증', type: 'question', text: '외국인등록증 재발급 절차를 알려주세요.' },
      { label: '📄 체류확인서', type: 'question', text: '체류확인서 발급 방법을 알려주세요.' },
      { label: '🔄 비자 변경', type: 'question', text: '비자 변경 절차를 알려주세요.' },
    ],
  },
  school: {
    id: 'school',
    name: '학교생활',
    icon: '🏫',
    iconBg: 'var(--c-green-l)',
    welcomeMsg: '학교생활 채널입니다. 수강신청, 학사 일정, 장학금, 기숙사 등 학교 관련 질문을 해주세요!',
    placeholder: '학교생활 관련 질문하기...',
    quickActions: [],
  },
  job: {
    id: 'job',
    name: '취업 & 아르바이트',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    welcomeMsg: '취업 & 아르바이트 채널입니다. 시간제 취업 허가, 아르바이트 규정, 인턴십 관련 질문을 해주세요!',
    placeholder: '취업 · 아르바이트 관련 질문하기...',
    quickActions: [],
  },
  house: {
    id: 'house',
    name: '주거',
    icon: '🏠',
    iconBg: 'var(--c-accent-l)',
    welcomeMsg: '주거 채널입니다. 전월세 계약, 관리비, 이사, 외국인 임대차 주의사항 등 주거 관련 질문을 해주세요!',
    placeholder: '주거 관련 질문하기...',
    quickActions: [],
  },
  insurance: {
    id: 'insurance',
    name: '병원 & 보험',
    icon: '🏥',
    iconBg: '#FEE2E2',
    welcomeMsg: '병원 & 보험 채널입니다. 건강보험 가입, 병원 이용 방법, 보험 혜택 등을 안내해 드립니다!',
    placeholder: '병원 · 보험 관련 질문하기...',
    quickActions: [],
  },
  main: {
    id: 'main',
    name: '메인 채팅',
    icon: '💬',
    iconBg: 'var(--c-accent-l)',
    welcomeMsg: '안녕하세요! 무엇이든 질문하세요. 적합한 채널로 안내해 드리겠습니다.',
    placeholder: '무엇이든 질문하세요...',
    quickActions: [],
  },
};

/** channelId로 채널 설정 조회 */
export function getChannel(id) {
  return CHANNELS[id] ?? null;
}
