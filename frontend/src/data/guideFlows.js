/**
 * src/data/guideFlows.js
 * ─────────────────────────────────────────────
 * 채널 상단 버튼(quickActions type 'flow')으로 시작하는 선택형 안내 트리.
 *
 * 버튼을 누르면 start 노드가 채팅에 AI 메시지로 나오고, 사용자가 options 중
 * 하나를 고르면 next 노드로 이어진다. checklist 가 있는 노드는 끝(leaf)이며,
 * 채팅에 체크리스트 카드가 붙고 FlowChecklistScreen 이 그 항목을 그린다.
 * (checklist 없는 leaf 는 안내 문구만 보여 준다)
 *
 * 문구 근거 — 지어낸 서류·금액은 넣지 않는다:
 *   재발급   하이코리아 「외국인등록증 발급/재발급/교부」
 *   연장     평가셋 v2 v_indb_10 · v_cplx_1 gold (동아대 비자 안내), 하이코리아 전자민원 목록
 *   변경     하이코리아 「체류자격변경」, 평가셋 v2 v_indb_5 · v_cplx_4 gold
 *   증명     부산출입국·외국인청 기관소개, 평가셋 v2 v_indb_9 gold
 *
 * FlowNode: { text, options?: {label, next}[], checklist?: Checklist }
 * Checklist: { title, sub, groups: { title, items: { text, sub? }[] }[] }
 */

// ── 공통 항목 ────────────────────────────────────────────────
const ARC_OFFICE = { text: '주소지 관할 출입국·외국인관서에 신청', sub: '부산: 부산출입국·외국인청 종합민원센터 (중구 중앙대로 146)' };
const ARC_RECEIVE = { text: '새 외국인등록증 수령' };
const ARC_PHOTO = { text: '컬러사진 1매 (3.5 × 4.5cm)', sub: '이전 사진이 6개월 이상 지난 경우' };
const arcDocs = extra => [
  { text: '여권' },
  { text: '재발급 신청서' },
  ARC_PHOTO,
  ...extra,
  { text: '수수료' },
];

const EXT_BASE = [
  { text: '통합신청서 · 사진' },
  { text: '외국인등록증 · 여권 사본' },
  { text: '재학증명서 · 성적증명서' },
  { text: '체류지 입증서류' },
  { text: '수수료' },
];
const EXT_APPLY = [
  { text: '체류기간 만료 전에 신청', sub: '하이코리아 전자민원(D-2 포함) 또는 출입국관서 방문예약' },
  { text: '심사 후 허가 확인' },
];

const CHG_APPLY = [
  { text: '새 활동을 시작하기 전에 신청', sub: '주소지 관할 출입국관리사무소 (하이코리아 전자민원도 가능)' },
  { text: '허가 확인', sub: '여권에 변경허가 날인, 외국인등록증에 허가사항 기재' },
];

const CERT_GROUPS = name => [
  { title: '준비', items: [
    { text: `제출처에서 요구하는 증명이 「${name}」인지 확인` },
    { text: '준비물은 방문 전 전화로 확인', sub: '종합민원센터 T. 051-461-3162~5' },
  ] },
  { title: '발급', items: [
    { text: '부산출입국·외국인청 종합민원센터 방문', sub: '부산 중구 중앙대로 146' },
    { text: `${name} 수령` },
  ] },
];

export const GUIDE_FLOWS = {
  'arc-renew': {
    start: 'reason',
    nodes: {
      reason: {
        text: '외국인등록증을 다시 받아야 하는 이유가 무엇인가요?',
        options: [
          { label: '잃어버렸어요',                     next: 'lost' },
          { label: '헐어서 못 쓰게 됐어요',             next: 'damaged' },
          { label: '기재할 칸이 부족해요',               next: 'full' },
          { label: '이름·국적 등 등록사항이 바뀌었어요', next: 'changed' },
        ],
      },
      lost: {
        text: '분실한 경우 여권, 신청서, 수수료에 더해\n- 분실 사유를 소명하는 자료\n가 필요해요. 이전 사진이 6개월 이상 지났다면 컬러사진 1매도 준비하세요.',
        checklist: {
          title: '외국인등록증 재발급 — 분실', sub: '하이코리아 재발급 안내 기준',
          groups: [
            { title: '서류 준비', items: arcDocs([{ text: '분실 사유를 소명하는 자료', sub: '분실한 경우에만 필요' }]) },
            { title: '신청', items: [ARC_OFFICE, ARC_RECEIVE] },
          ],
        },
      },
      damaged: {
        text: '헐어서 못 쓰게 된 경우 여권, 신청서, 수수료와 함께\n- 기존(구) 외국인등록증\n을 제출해야 해요. 이전 사진이 6개월 이상 지났다면 컬러사진 1매도 필요해요.',
        checklist: {
          title: '외국인등록증 재발급 — 훼손', sub: '하이코리아 재발급 안내 기준',
          groups: [
            { title: '서류 준비', items: arcDocs([{ text: '기존(구) 외국인등록증', sub: '헐어서 못 쓰게 된 카드 그대로' }]) },
            { title: '신청', items: [ARC_OFFICE, ARC_RECEIVE] },
          ],
        },
      },
      full: {
        text: '기재할 칸이 부족한 경우 여권, 신청서, 수수료와 함께\n- 기존(구) 외국인등록증\n을 제출해야 해요. 이전 사진이 6개월 이상 지났다면 컬러사진 1매도 필요해요.',
        checklist: {
          title: '외국인등록증 재발급 — 기재란 부족', sub: '하이코리아 재발급 안내 기준',
          groups: [
            { title: '서류 준비', items: arcDocs([{ text: '기존(구) 외국인등록증' }]) },
            { title: '신청', items: [ARC_OFFICE, ARC_RECEIVE] },
          ],
        },
      },
      changed: {
        text: '성명·성별·생년월일·국적이 바뀐 경우\n- 사유가 생긴 날부터 15일 이내\n에 신청해야 해요. 여권, 신청서, 수수료와 함께 기존(구) 외국인등록증을 제출하세요.',
        checklist: {
          title: '외국인등록증 재발급 — 등록사항 변경', sub: '하이코리아 재발급 안내 기준',
          groups: [
            { title: '서류 준비', items: arcDocs([{ text: '기존(구) 외국인등록증' }]) },
            { title: '신청', items: [
              { text: '사유 발생일부터 15일 이내 신청', sub: '성명·성별·생년월일·국적 변경' },
              ARC_OFFICE, ARC_RECEIVE,
            ] },
          ],
        },
      },
    },
  },

  'visa-extension': {
    start: 'status',
    nodes: {
      status: {
        text: 'D-2 체류기간 연장을 안내할게요. 지금 학업 상태가 어디에 해당하나요?',
        options: [
          { label: '정상 재학 중이에요',                 next: 'normal' },
          { label: '성적 2.0 미만 · 초과학기 · 졸업유예', next: 'special' },
        ],
      },
      normal: {
        text: '체류기간이 끝나기 전에 신청해야 해요. 기본 서류는\n- 통합신청서 · 사진\n- 외국인등록증 · 여권 사본\n- 재학증명서 · 성적증명서\n- 체류지 입증서류 · 수수료\n예요.',
        checklist: {
          title: 'D-2 체류기간 연장 — 정상 재학', sub: '동아대 비자 안내 기준',
          groups: [
            { title: '서류 준비', items: EXT_BASE },
            { title: '신청', items: EXT_APPLY },
          ],
        },
      },
      special: {
        text: '기본 서류에 더해\n- 은행 잔고증명\n- 사유서\n- 지도교수 확인서\n등이 추가될 수 있어요. 최종 판단은 출입국관서가 하니 국제교류과에 먼저 확인하세요.',
        checklist: {
          title: 'D-2 체류기간 연장 — 성적·학기 예외', sub: '동아대 비자 안내 기준 · 최종 판단은 출입국관서',
          groups: [
            { title: '서류 준비', items: EXT_BASE },
            { title: '추가될 수 있는 서류', items: [
              { text: '은행 잔고증명' },
              { text: '사유서' },
              { text: '지도교수 확인서' },
              { text: '국제교류과에 추가 서류 확인' },
            ] },
            { title: '신청', items: EXT_APPLY },
          ],
        },
      },
    },
  },

  'status-change': {
    start: 'kind',
    nodes: {
      kind: {
        text: '어떤 체류자격으로 바꾸려고 하나요?',
        options: [
          { label: 'D-4 어학연수 → D-2 유학', next: 'd4d2' },
          { label: '다른 체류자격으로',        next: 'other' },
        ],
      },
      d4d2: {
        text: '어학연수를 마치고 대학에 입학하면 출국하지 않고 국내에서 체류자격 변경허가를 받을 수 있어요. 단, 유학 활동을 시작하기 전에 허가를 받아야 해요.',
        checklist: {
          title: '체류자격 변경 — D-4 → D-2', sub: '하이코리아 · 동아대 비자 안내 기준',
          groups: [
            { title: '서류 준비', items: [
              { text: '신청서 · 사진' },
              { text: '여권 사본 · 외국인등록증' },
              { text: '체류지 입증서류' },
              { text: '잔고증명' },
              { text: '학력입증서류' },
              { text: '어학연수 출석증명' },
              { text: '등록금 납부증명' },
            ] },
            { title: '신청', items: CHG_APPLY },
          ],
        },
      },
      other: {
        text: '원칙적으로는 출국 후 새 사증(VISA)을 받아 입국해야 해요. 국내에서 요건을 갖출 수 있으면 엄격한 심사를 거쳐 제한적으로 변경할 수 있어요.\n\n자격별 제출서류가 달라서, 관할 출입국관리사무소에 먼저 문의하세요.',
        checklist: {
          title: '체류자격 변경 — 기타 자격', sub: '하이코리아 체류자격변경 안내 기준',
          groups: [
            { title: '서류 준비', items: [
              { text: '체류자격변경허가 신청서' },
              { text: '여권' },
              { text: '외국인등록증', sub: '해당자' },
              { text: '체류자격별 첨부서류', sub: '관할 출입국관리사무소에 확인' },
              { text: '수수료' },
            ] },
            { title: '신청', items: CHG_APPLY },
          ],
        },
      },
    },
  },

  'stay-cert': {
    start: 'which',
    nodes: {
      which: {
        text: '출입국관서에서 발급하는 증명은 여러 가지예요. 어떤 게 필요하세요?',
        options: [
          { label: '외국인등록사실증명', next: 'reg' },
          { label: '출입국사실증명',     next: 'entry' },
          { label: '잘 모르겠어요',      next: 'unsure' },
        ],
      },
      reg: {
        text: '외국인등록사실증명은 부산출입국·외국인청 종합민원센터에서 발급해요. 준비물은 방문 전에 전화로 확인하세요.\n- 부산 중구 중앙대로 146\n- T. 051-461-3162~5',
        checklist: { title: '외국인등록사실증명 발급', sub: '부산출입국·외국인청 기준', groups: CERT_GROUPS('외국인등록사실증명') },
      },
      entry: {
        text: '출입국사실증명은 부산출입국·외국인청 종합민원센터에서 발급해요. 준비물은 방문 전에 전화로 확인하세요.\n- 부산 중구 중앙대로 146\n- T. 051-461-3162~5',
        checklist: { title: '출입국사실증명 발급', sub: '부산출입국·외국인청 기준', groups: CERT_GROUPS('출입국사실증명') },
      },
      unsure: {
        text: '서류를 내야 하는 곳(학교·은행·회사 등)에 필요한 증명의 정확한 이름을 먼저 물어보세요. 이름을 알려주시면 아래 입력창에서 더 자세히 안내해 드릴게요.',
      },
    },
  },
};
