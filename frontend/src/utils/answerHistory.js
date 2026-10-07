/**
 * src/utils/answerHistory.js
 * ─────────────────────────────────────────────
 * "기록" 탭(SearchScreen)에 보여줄 실제 질문/답변 목록을
 * 채팅 상태(chatState)에서 그대로 뽑아낸다.
 *
 * 따로 저장소를 새로 만들지 않는다 — AppContext의 chatState(채널별
 * 메시지 배열)가 이미 실제 대화 내용을 들고 있으므로, 거기서 AI 답변과
 * 그 직전 사용자 질문을 짝지어 꺼내기만 하면 된다. (순수 함수라 React
 * 없이도 테스트 가능.)
 *
 * @param {Record<string, Array<{id,role,text,tags,createdAt}>>} chatState
 * @returns {Array<{ channelId, messageId, question, answer, tags, createdAt }>}
 *          최신 답변이 먼저 오도록 정렬됨
 */
export function buildAnswerHistory(chatState) {
  const list = [];

  Object.entries(chatState).forEach(([channelId, msgs]) => {
    msgs.forEach((msg, i) => {
      if (msg.role !== 'ai') return;

      // 같은 채널 메시지 배열에서 이 AI 답변 바로 앞에 있는 사용자 질문을 찾는다
      const question = msgs.slice(0, i).reverse().find(m => m.role === 'user');
      if (!question) return; // 질문 없이 나온 AI 메시지는 "답변 기록"으로 안 침

      list.push({
        channelId,
        messageId: msg.id,
        question: question.text,
        answer: msg.text,
        tags: msg.tags ?? [],
        createdAt: msg.createdAt ?? 0,
      });
    });
  });

  return list.sort((a, b) => b.createdAt - a.createdAt);
}
