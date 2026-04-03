/**
 * src/data/channels.js
 * ─────────────────────────────────────────────
 * 채널 데이터 단일 소스 (data layer)
 *
 * 백엔드 GET /channels 응답과 동일한 구조로 맞춰두었습니다.
 * 실제 API 연결 시 이 파일 대신 fetch 응답을 그대로 사용하면 됩니다.
 *
 * Channel 타입 정의:
 * {
 *   id          : string   — 고유 식별자 (라우팅/API 키)
 *   name        : string   — 화면에 표시할 채널명
 *   icon        : string   — 이모지 아이콘
 *   iconBg      : string   — 아이콘 배경 색상 (CSS 변수 or hex)
 *   placeholder : string   — 채팅 입력창 placeholder
 *   welcomeMsg  : string   — 채널 진입 시 첫 AI 메시지
 *   quickActions: Array    — 상단 퀵버튼 (선택)
 * }
 */

export const CHANNEL_LIST = [
  {
    id: 'visa',
    name: '비자 & 체류',
    icon: '🛂',
    iconBg: 'var(--c-purple-l)',
    placeholder: '비자 관련 질문하기...',
    welcomeMsg: 'D-2 채널입니다. 만료까지 87일 남았어요. 위 버튼을 탭하거나 직접 질문해주세요!',
    quickActions: [
      { label: '📋 비자 연장 절차', type: 'navigate', target: 's-step' },
      { label: '🪪 외국인등록증',   type: 'question', text: '외국인등록증 재발급 절차를 알려주세요.' },
      { label: '📄 체류확인서',     type: 'question', text: '체류확인서 발급 방법을 알려주세요.' },
      { label: '🔄 비자 변경',      type: 'question', text: '비자 변경 절차를 알려주세요.' },
    ],
  },
  {
    id: 'school',
    name: '학교생활',
    icon: '🏫',
    iconBg: 'var(--c-green-l)',
    placeholder: '학교생활 관련 질문하기...',
    welcomeMsg: '학교생활 채널입니다. 수강신청, 학사 일정, 장학금, 기숙사 등 학교 관련 질문을 해주세요!',
    quickActions: [],
  },
  {
    id: 'job',
    name: '취업 & 아르바이트',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    placeholder: '취업 · 아르바이트 관련 질문하기...',
    welcomeMsg: '취업 & 아르바이트 채널입니다. 시간제 취업 허가, 아르바이트 규정, 인턴십 관련 질문을 해주세요!',
    quickActions: [],
  },
  {
    id: 'house',
    name: '주거',
    icon: '🏠',
    iconBg: 'var(--c-accent-l)',
    placeholder: '주거 관련 질문하기...',
    welcomeMsg: '주거 채널입니다. 전월세 계약, 관리비, 이사, 외국인 임대차 주의사항 등 주거 관련 질문을 해주세요!',
    quickActions: [],
  },
  {
    id: 'insurance',
    name: '병원 & 보험',
    icon: '🏥',
    iconBg: '#FEE2E2',
    placeholder: '병원 · 보험 관련 질문하기...',
    welcomeMsg: '병원 & 보험 채널입니다. 건강보험 가입, 병원 이용 방법, 보험 혜택 등을 안내해 드립니다!',
    quickActions: [],
  },
  {
    id: 'main',
    name: '메인 채팅',
    icon: '💬',
    iconBg: 'var(--c-accent-l)',
    placeholder: '무엇이든 질문하세요...',
    welcomeMsg: '안녕하세요! 무엇이든 질문하세요. 적합한 채널로 안내해 드리겠습니다.',
    quickActions: [],
  },
];

/**
 * id로 채널 단건 조회
 * @param {string} id
 * @returns {object|null}
 */
export function getChannelById(id) {
  return CHANNEL_LIST.find(ch => ch.id === id) ?? null;
}
