/**
 * src/data/mockMessages.js
 * ─────────────────────────────────────────────
 * 개발/테스트용 mock 메시지 & 출처 데이터
 *
 * 백엔드 연결 후 이 파일은 삭제하거나 테스트 전용으로만 사용합니다.
 *
 * ── 타입 정의 ──────────────────────────────────
 *
 * Message:
 * {
 *   id        : string          — "{channelId}-{timestamp}-{role}"
 *   channelId : string          — 어느 채널의 메시지인지
 *   role      : 'user' | 'ai'  — 발화자
 *   text      : string          — 메시지 본문
 *   sources   : Source[]        — RAG 출처 목록 (AI 응답에만 포함)
 *   createdAt : number          — Unix timestamp (ms)
 * }
 *
 * Source:
 * {
 *   id     : string   — 출처 고유 ID
 *   label  : string   — 출처 제목/기관명
 *   detail : string   — 출처 상세 설명 (조항, 날짜 등)
 *   url    : string   — 원문 링크 (없으면 빈 문자열)
 * }
 */

// ── Mock Source 샘플 ───────────────────────────────────────────────────────

export const MOCK_SOURCES = {
  visa: [
    {
      id: 'src-visa-1',
      label: '법무부 출입국관리법 시행규칙 (2024)',
      detail: '제76조 – 체류자격 변경·연장 절차 및 제출서류',
      url: '',
    },
    {
      id: 'src-visa-2',
      label: 'Hi Korea 외국인 종합안내',
      detail: 'www.hikorea.go.kr · 비자 연장 온라인 신청 가이드',
      url: 'https://www.hikorea.go.kr',
    },
  ],
  school: [
    {
      id: 'src-school-1',
      label: '부산대학교 학사운영규정',
      detail: '제12조 – 수강신청 및 변경 절차',
      url: '',
    },
  ],
  job: [
    {
      id: 'src-job-1',
      label: '출입국관리법 시행령 제23조',
      detail: '유학생 시간제 취업 허가 기준 (주 20시간)',
      url: '',
    },
  ],
  house: [
    {
      id: 'src-house-1',
      label: '주택임대차보호법 제3조',
      detail: '전입신고 및 확정일자 요건',
      url: '',
    },
  ],
  insurance: [
    {
      id: 'src-insurance-1',
      label: '국민건강보험법 시행령',
      detail: '외국인 유학생 건강보험 의무가입 기준 (6개월 이상 체류)',
      url: 'https://www.nhis.or.kr',
    },
  ],
  main: [],
};

// ── Mock AI 응답 텍스트 풀 ────────────────────────────────────────────────

export const MOCK_ANSWER_POOL = {
  // ── 비자 & 체류 채널 ──────────────────────────────────────────────────────
  visa: [
    // [0] 시나리오 1 핵심: ARC 재등록 서류
    'ARC 재등록 시 기본적으로 필요한 서류는 아래와 같아요.\n\n1. 여권 (유효기간 확인)\n2. 외국인등록증\n3. 재학증명서\n4. 체류지 관련 서류 (필요 시)\n5. 수수료\n\n추가 안내:\n- Hi Korea 온라인 신청 또는 출입국관리사무소 방문 신청 가능해요.\n- 비자 만료 전에 미리 신청하는 것이 중요합니다.\n\n#ARC #재등록 #비자 #HiKorea',
    // [1] 외국인등록증 분실·재발급
    '외국인등록증을 분실했다면 아래 순서로 진행하면 돼요.\n\n1. 분실 사실 확인 후 재발급 신청 준비\n2. 여권, 사진, 재발급 신청서 등 필요 서류 준비\n3. Hi Korea에서 방문 예약\n4. 출입국관리사무소 방문 후 재발급 신청\n5. 새 외국인등록증 수령\n\n주의사항:\n- 분실 후 오래 방치하지 않는 것이 좋아요.\n- 신분 확인이 필요할 수 있으니 여권을 함께 챙겨두세요.\n\n준비할 서류를 체크리스트로 정리해 드릴까요?\n\n#외국인등록증 #분실 #재발급 #출입국',
    // [2] D-2 비자 연장 절차
    'D-2 비자 연장은 보통 아래 순서로 진행돼요.\n\n1. 여권, 외국인등록증, 재학증명서 등 기본 서류 준비\n2. Hi Korea에서 온라인 신청 가능 여부 확인 또는 방문 예약\n3. 출입국관리사무소 방문 또는 온라인 접수\n4. 수수료 납부 및 접수 완료\n5. 처리 결과 확인\n\n주의사항:\n- 비자 만료 전에 미리 신청해야 해요.\n- 학교별로 추가 서류가 필요할 수 있어요.\n\n#D-2 #비자연장 #서류 #HiKorea',
  ],
  // ── 학교생활 채널 ─────────────────────────────────────────────────────────
  school: [
    // [0] 시나리오 2 핵심: 수강신청 준비
    '수강신청 전에 아래 내용을 먼저 준비하면 좋아요.\n\n1. 학교 포털 로그인 확인\n2. 수강신청 날짜 확인\n3. 시간표 미리 계획\n4. 전공/교양 이수 조건 확인\n\n추가 안내:\n- 신청 시작 시간에 맞춰 빠르게 진행하는 것이 중요합니다.\n- 인기 과목은 빠르게 마감될 수 있습니다.\n- 수강정정 기간에 변경 가능합니다.\n\n준비 단계를 체크리스트로 정리해 드릴까요?\n\n#수강신청 #학교생활 #학사일정',
    // [1] 등록금 + 수강신청 복합
    '다음 학기 준비는 등록금 납부와 수강신청을 나누어 확인하면 좋아요.\n\n1. 학사일정에서 등록금 납부 기간 확인\n2. 등록금 고지서 확인 후 납부\n3. 수강신청 기간 확인\n4. 학교 포털에서 희망 과목 검색\n5. 수강신청 완료 후 시간표 확인\n6. 필요하면 수강정정 기간에 변경\n\n주의사항:\n- 등록금 납부 기간과 수강신청 기간은 다를 수 있어요.\n- 유학생은 국제처 공지도 함께 확인하는 것이 좋아요.\n\n준비 단계를 체크리스트로 정리해 드릴까요?\n\n#등록금 #수강신청 #학사일정 #학교생활',
  ],
  // ── 취업 & 아르바이트 채널 ────────────────────────────────────────────────
  job: [
    '유학생 아르바이트를 시작하려면 먼저 시간제 취업 허가가 필요해요.\n\n1. 출입국사무소 방문 또는 Hi Korea 온라인 신청\n2. 재학증명서 + 학업성적표 + 여권 + 외국인등록증 준비\n3. 허가증 수령 후 취업 가능\n\nD-2 비자 기준 학기 중 주 20시간, 방학 중 주 40시간까지 가능합니다.\n\n#알바 #시간제취업 #유학생',
    '불법 취업 시 비자 취소 및 강제 출국 처분을 받을 수 있으니 반드시 허가 후 취업하세요.\n\n#주의사항 #취업규정',
  ],
  // ── 주거 채널 ─────────────────────────────────────────────────────────────
  house: [
    '전월세 계약 전 등기부등본을 꼭 확인하세요. 근저당 설정 여부를 반드시 체크해야 합니다.\n\n#전세 #월세 #계약주의',
    '전입신고는 계약 후 14일 이내에 주민센터에서 해야 법적 보호를 받을 수 있습니다.\n\n#전입신고 #주거권리',
  ],
  // ── 병원 & 보험 채널 ──────────────────────────────────────────────────────
  insurance: [
    '유학생 보험 가입 방법은 학교 공지나 보험 정책에 따라 달라질 수 있어요.\n최신 기준 확인이 필요한 항목은 아래와 같아요.\n\n1. 부산대학교 국제처 또는 관련 부서 공지 확인\n2. 유학생 보험 가입 대상 확인\n3. 가입 기간과 보험료 확인\n4. 제출 서류 또는 온라인 신청 여부 확인\n5. 가입 완료 후 증빙 자료 보관\n\n⚠️ 현재 DB에 없는 최신 정보일 수 있어 공식 공지 확인이 필요합니다.\n\n#유학생보험 #부산대학교 #최신공지 #웹검색필요',
    '6개월 이상 체류하는 외국인 유학생은 건강보험 가입이 의무입니다.\n국민건강보험공단(nhis.or.kr)에서 온라인으로 가입 신청할 수 있습니다.\n\n#건강보험 #유학생의무',
  ],
  // ── 메인채팅 ──────────────────────────────────────────────────────────────
  main: [
    // [0] 시나리오 1: ARC 재등록 → 비자 채널 유도
    'ARC 재등록은 준비서류와 신청 절차를 함께 확인해야 해요.\n비자 & 체류 채널에서 단계별로 자세히 안내해드릴게요.',
    // [1] 시나리오 2: 수강신청 준비 → 학교생활 채널 유도
    '수강신청은 학사 일정과 신청 방법을 함께 확인해야 해요.\n학교생활 채널에서 단계별로 안내해드릴게요.',
    // [2] D-2 비자 연장 → 비자 채널 유도
    'D-2 비자 연장은 준비서류와 신청 절차를 함께 확인해야 해요.\n비자 & 체류 채널에서 단계별로 안내해드릴게요.',
    // [3] 외국인등록증 분실 → 비자 채널 유도
    '외국인등록증 분실은 빠르게 재발급 신청을 해야 해요.\n비자 & 체류 채널에서 신고와 재발급 절차를 정리해드릴게요.',
    // [4] 등록금+수강신청 복합 → 학교생활 채널 유도
    '이 질문은 등록금 납부와 수강신청이 함께 포함된 학사 일정 질문이에요.\n학교생활 채널에서 일정과 절차를 묶어서 안내해드릴게요.',
    // [5] 유학생 보험 → 병원 & 보험 채널 유도
    '이 질문은 최신 공지 확인이 필요한 내용이에요.\n현재 데이터에 없거나 기준이 바뀔 수 있어서 병원 & 보험 채널에서 최신 정보를 확인하는 흐름으로 안내할게요.',
  ],
};

// ── 채널별 기본 체크리스트 ID ────────────────────────────────────────────────
// 키워드 매칭과 무관하게 채널 자체에 연결된 기본 체크리스트
const CHANNEL_DEFAULT_CHECKLIST = {
  visa:   'visa-extension',
  school: 'school-registration',
};

// ── 데모용 키워드 → 응답 인덱스 매핑 ────────────────────────────────────────
// message 키워드에 맞는 응답을 결정적으로 선택하기 위한 구조
// checklistId: 해당 응답과 함께 생성할 체크리스트 (없으면 채널 기본값 사용)
const DEMO_PICK_RULES = {
  main: [
    { keywords: ['arc', 'ARC', '재등록'], index: 0 },
    { keywords: ['수강신청', '수강', '준비', '학교'], index: 1 },
    { keywords: ['비자', '연장', 'D-2', 'd-2', '절차'], index: 2 },
    { keywords: ['외국인등록증', '분실', '재발급'], index: 3 },
    { keywords: ['등록금', '납부', '다음 학기'], index: 4 },
    { keywords: ['보험', '부산대', '최신'], index: 5 },
  ],
  visa: [
    { keywords: ['외국인등록증', '분실', '재발급', 'arc', 'ARC', '재등록'], index: 1, checklistId: 'arc-renew' },
    { keywords: ['비자', '연장', 'D-2', 'd-2', '서류', '체크리스트'],       index: 2, checklistId: 'visa-extension' },
  ],
  school: [
    { keywords: ['등록금', '납부', '다음 학기'],            index: 1, checklistId: 'school-registration' },
    { keywords: ['수강신청', '수강', '준비', '체크리스트'], index: 0, checklistId: 'school-registration' },
  ],
  insurance: [
    { keywords: ['부산대', '최신', '유학생 보험', '보험 가입'], index: 0 },
  ],
};

/**
 * 채널 ID + 사용자 메시지로 데모 응답 선택
 * 키워드가 일치하면 해당 응답, 없으면 풀 첫 번째 항목 반환
 * @param {string} channelId
 * @param {string} [message]
 * @returns {{ text: string, sources: Source[] }}
 */
export function pickMockResponse(channelId, message = '') {
  const pool    = MOCK_ANSWER_POOL[channelId] ?? MOCK_ANSWER_POOL.main;
  const rules   = DEMO_PICK_RULES[channelId] ?? [];
  const lower   = message.toLowerCase();

  let index       = 0;
  let checklistId = CHANNEL_DEFAULT_CHECKLIST[channelId] ?? null;

  for (const rule of rules) {
    if (rule.keywords.some(kw => lower.includes(kw.toLowerCase()))) {
      index       = rule.index;
      checklistId = rule.checklistId ?? checklistId;
      break;
    }
  }

  const text    = pool[index] ?? pool[0];
  const sources = MOCK_SOURCES[channelId] ?? [];
  return { text, sources, checklistId };
}

/**
 * 새 Message 객체 생성 헬퍼
 * @param {{ channelId: string, role: 'user'|'ai', text: string, sources?: object[] }} params
 * @returns {Message}
 */
export function createMessage({ channelId, role, text, sources = [] }) {
  return {
    id: `${channelId}-${Date.now()}-${role}`,
    channelId,
    role,
    text,
    sources,
    createdAt: Date.now(),
  };
}
