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
  visa: [
    'D-2 비자 연장은 만료일 4개월 전부터 신청 가능합니다. 하이코리아(hikorea.go.kr)에서 온라인 신청하거나 관할 출입국사무소를 방문하세요.',
    '외국인등록증 재발급은 출입국사무소 방문 또는 하이코리아 온라인 신청으로 가능합니다. 수수료는 3만 원입니다.',
    '체류 기간 연장 신청 시 여권 원본, 외국인등록증, 재학증명서(영문), 수수료 6만 원이 필요합니다.',
    '시간제 취업 허가를 받으려면 재학 중인 대학의 확인서와 여권, 외국인등록증이 필요합니다.',
  ],
  school: [
    '수강신청은 보통 학기 시작 2~3주 전에 진행됩니다. 학교 포털에서 시간표를 확인하고 원하는 강의를 신청하세요.',
    '장학금은 교내·교외 두 가지로 나뉩니다. 교내는 성적 기준, 교외는 별도 공고를 확인하세요.',
    '기숙사 신청은 학교 생활관 홈페이지에서 합니다. 외국인 유학생 전용 기숙사를 운영하는 학교도 있습니다.',
    '학사 일정은 학교 공식 홈페이지의 학사력을 참고하세요. 휴학·복학·수강 취소 기간을 꼭 확인하세요.',
  ],
  job: [
    'D-2 비자 유학생은 시간제 취업 허가를 받으면 주 20시간 이내로 아르바이트가 가능합니다.',
    '시간제 취업 허가는 재학증명서·학업성적표를 지참해 출입국사무소에 신청하면 됩니다.',
    '불법 취업 시 비자 취소 및 강제 출국 처분을 받을 수 있으니 반드시 허가 후 취업하세요.',
    '방학 중에는 주 40시간까지 취업이 가능합니다.',
  ],
  house: [
    '전월세 계약 전 등기부등본을 꼭 확인하세요. 근저당 설정 여부를 반드시 체크해야 합니다.',
    '전입신고는 계약 후 14일 이내에 주민센터에서 해야 법적 보호를 받을 수 있습니다.',
    '관리비 항목(인터넷, 주차, 청소비 등)이 계약서에 명시되어 있는지 미리 확인하세요.',
    '외국인이 한국에서 전월세 계약 시 집주인 동의 없이는 전대가 불가능합니다.',
  ],
  insurance: [
    '6개월 이상 체류하는 외국인 유학생은 건강보험 가입이 의무입니다.',
    '국민건강보험공단(nhis.or.kr)에서 온라인으로 가입 신청할 수 있습니다.',
    '병원 방문 시 건강보험카드(또는 외국인등록증)와 여권을 함께 지참하세요.',
    '처방을 받으려면 먼저 내과·가정의학과에서 진료 후 처방전을 발급받아야 합니다.',
  ],
  main: [
    '채널별로 질문하면 더 정확한 답변을 받을 수 있어요. 비자, 학교, 취업, 주거, 병원 채널을 이용해 보세요.',
    '유학생에게 필요한 정보는 비자 & 체류 채널에서 자세히 안내해 드립니다.',
    '궁금한 사항이 있으면 해당 채널로 이동해 더 전문적인 답변을 받아보세요.',
  ],
};

/**
 * 채널 ID로 랜덤 mock 응답 하나 선택
 * @param {string} channelId
 * @returns {{ text: string, sources: Source[] }}
 */
export function pickMockResponse(channelId) {
  const pool = MOCK_ANSWER_POOL[channelId] ?? MOCK_ANSWER_POOL.main;
  const text  = pool[Math.floor(Math.random() * pool.length)];
  const sources = MOCK_SOURCES[channelId] ?? [];
  return { text, sources };
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
