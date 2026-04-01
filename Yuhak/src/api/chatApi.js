import { BASE_URL } from './config';

/**
 * 채널별 mock 응답 풀
 * 실제 API 연결 후 이 섹션은 전부 제거
 */
const MOCK_POOL = {
  visa: [
    'D-2 비자 연장은 만료일 4개월 전부터 신청 가능합니다. 하이코리아(www.hikorea.go.kr)에서 온라인 신청하거나, 관할 출입국사무소를 방문하세요.',
    '시간제 취업 허가를 받으려면 재학 중인 대학의 확인서와 여권, 외국인등록증이 필요합니다.',
    '외국인등록증 재발급은 출입국사무소에 직접 방문하거나 하이코리아를 통해 신청할 수 있습니다. 수수료는 3만원입니다.',
    '체류 기간 연장 신청 시 표준 규격 사진 1매, 수수료(6만원), 재학증명서가 필요합니다.',
  ],
  school: [
    '수강신청은 보통 학기 시작 2~3주 전에 진행됩니다. 학교 포털에서 시간표를 확인하고 원하는 강의를 신청하세요.',
    '장학금은 교내 장학금과 교외 장학금으로 나뉩니다. 교내 장학금은 성적 기준, 교외는 별도 공고를 확인하세요.',
    '기숙사 신청은 학교 생활관 홈페이지에서 할 수 있습니다. 외국인 유학생 전용 기숙사를 운영하는 학교도 있습니다.',
    '학사 일정은 학교 공식 홈페이지의 학사력을 참고하세요. 휴학, 복학, 수강 취소 기간을 꼭 확인하세요.',
  ],
  job: [
    'D-2 비자 유학생은 시간제 취업 허가를 받으면 주 20시간 이내로 아르바이트가 가능합니다.',
    '시간제 취업 허가는 대학에서 발급한 재학증명서와 학업성적표를 가지고 출입국사무소에 신청하면 됩니다.',
    '불법 취업 시 비자 취소 및 강제 출국 처분을 받을 수 있으니, 반드시 허가 후 취업하세요.',
    '방학 중에는 주 40시간까지 취업이 가능합니다. 단, 학교에 방학 기간을 확인하는 서류가 필요할 수 있습니다.',
  ],
  house: [
    '외국인이 한국에서 전월세 계약 시 집주인 동의 없이는 전대가 불가능합니다.',
    '계약 전 등기부등본을 꼭 확인하세요. 근저당 설정 여부를 반드시 체크해야 합니다.',
    '전입신고는 계약 후 14일 이내에 주민센터에서 해야 법적 보호를 받을 수 있습니다.',
    '관리비 항목은 계약서에 명시되어야 합니다. 인터넷, 주차, 청소비 등이 포함되는지 미리 확인하세요.',
  ],
  insurance: [
    '6개월 이상 체류하는 외국인 유학생은 건강보험 가입이 의무입니다.',
    '국민건강보험은 국민건강보험공단(nhis.or.kr)에서 가입 신청할 수 있습니다.',
    '병원 방문 시 건강보험카드(또는 외국인등록증)와 여권을 함께 지참하세요.',
    '의약품 처방을 받으려면 먼저 내과 또는 가정의학과에서 진료를 받고 처방전을 발급받아야 합니다.',
  ],
  main: [
    '질문을 채널별로 분류하면 더 정확한 답변을 받을 수 있어요. 비자, 학교생활, 취업, 주거, 병원 채널을 이용해 보세요.',
    '유학생에게 필요한 정보는 비자 & 체류 채널에서 자세히 안내해 드립니다.',
    '궁금한 사항이 있으시면 해당 채널로 이동하여 더 전문적인 답변을 받으세요.',
  ],
};

function pickMock(channelId) {
  const pool = MOCK_POOL[channelId] ?? MOCK_POOL.main;
  return pool[Math.floor(Math.random() * pool.length)];
}

/**
 * AI에게 메시지 전송
 *
 * @param {object} params
 * @param {string} params.channelId  - 채널 식별자
 * @param {string} params.message   - 사용자 입력 텍스트
 * @param {Array}  params.history   - 이전 대화 내역 [{ role, content }]
 * @returns {Promise<{ answer: string, tags: string[] }>}
 */
export async function sendMessage({ channelId, message, history }) {
  try {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channelId, message, history }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    return {
      answer: data.answer ?? '',
      tags: data.tags ?? [],
    };
  } catch {
    // API 미연결 시 mock 응답 (실제 API 연결 후 이 블록 제거)
    await new Promise(r => setTimeout(r, 700));
    return { answer: pickMock(channelId), tags: [] };
  }
}
