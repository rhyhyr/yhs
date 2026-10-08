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
    welcomeMsg: '비자 & 체류 채널입니다.\nARC 재등록, 비자 연장, 외국인등록증 관련 절차를 안내해드릴게요.',
    placeholder: '비자 관련 질문하기...',
    quickActions: [
      { label: '📋 비자 연장 절차', type: 'navigate', target: 's-step' },
      { label: '🪪 외국인등록증 재발급', type: 'navigate', target: 's-arc-checklist' },
      { label: '📄 체류확인서', type: 'question', text: '체류확인서 발급 방법을 알려주세요.' },
      { label: '🔄 비자 변경', type: 'question', text: '비자 변경 절차를 알려주세요.' },
    ],
  },
  school: {
    id: 'school',
    name: '학교생활',
    icon: '🏫',
    iconBg: 'var(--c-green-l)',
    welcomeMsg: '학교생활 채널입니다.\n수강신청, 학사 일정, 장학금, 기숙사 등 학교 관련 정보를 단계별로 안내해드릴게요.',
    placeholder: '학교생활 관련 질문하기...',
    quickActions: [
      { label: '📋 수강신청 체크리스트', type: 'navigate', target: 's-school-checklist' },
      { label: '📅 학사일정 확인',       type: 'question', text: '이번 학기 학사일정 알려주세요.' },
      { label: '💰 등록금 납부',         type: 'question', text: '등록금 납부 방법을 알려주세요.' },
      { label: '🎓 장학금 안내',         type: 'question', text: '유학생 장학금 신청 방법을 알려주세요.' },
    ],
  },
  job: {
    id: 'job',
    name: '취업 & 아르바이트',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    welcomeMsg: '취업 & 아르바이트 채널입니다.\n시간제 취업 허가 절차, 필요 서류, 근무 가능 시간 등을 단계별로 안내해드릴게요.',
    placeholder: '취업 · 아르바이트 관련 질문하기...',
    quickActions: [
      { label: '🪪 시간제취업 허가', type: 'question', text: '시간제 취업 허가 신청 방법을 알려주세요.' },
      { label: '📄 필요 서류',       type: 'question', text: '아르바이트 하려면 어떤 서류가 필요해요?' },
      { label: '⏰ 근무 가능 시간',  type: 'question', text: '학기 중 아르바이트 가능한 시간이 얼마나 되나요?' },
      { label: '⚠️ 불법 취업 주의',  type: 'question', text: '허가 없이 일하면 어떻게 되나요?' },
    ],
  },
  house: {
    id: 'house',
    name: '주거',
    icon: '🏠',
    iconBg: 'var(--c-accent-l)',
    welcomeMsg: '주거 채널입니다. 전월세 계약, 관리비, 이사, 외국인 임대차 주의사항 등 주거 관련 질문을 해주세요!',
    placeholder: '주거 관련 질문하기...',
    quickActions: [
      { label: '📑 계약 전 확인사항', type: 'question', text: '전월세 계약할 때 뭘 확인해야 하나요?' },
      { label: '🏠 전입신고',         type: 'question', text: '전입신고는 어떻게 하나요?' },
      { label: '💰 관리비',           type: 'question', text: '관리비에는 보통 뭐가 포함되나요?' },
      { label: '📦 이사 체크리스트',  type: 'question', text: '이사할 때 주의할 점을 알려주세요.' },
    ],
  },
  insurance: {
    id: 'insurance',
    name: '병원 & 보험',
    icon: '🏥',
    iconBg: '#FEE2E2',
    welcomeMsg: '병원 & 보험 채널입니다. 건강보험 가입, 병원 이용 방법, 보험 혜택 등을 안내해 드립니다!',
    placeholder: '병원 · 보험 관련 질문하기...',
    quickActions: [
      { label: '🏥 건강보험 가입', type: 'question', text: '외국인 유학생 건강보험 가입 방법을 알려주세요.' },
      { label: '💳 보험료 납부',   type: 'question', text: '건강보험료는 어떻게 납부하나요?' },
      { label: '🩺 병원 이용',     type: 'question', text: '한국에서 병원은 어떻게 이용하나요?' },
      { label: '📋 보험 혜택',     type: 'question', text: '건강보험으로 어떤 혜택을 받을 수 있나요?' },
    ],
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
