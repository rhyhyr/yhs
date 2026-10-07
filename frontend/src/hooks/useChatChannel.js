import { useState } from 'react';
import { useApp } from './useApp';
import { sendMessage } from '../api/chat';

/**
 * 채널 채팅 공통 로직 훅
 *
 * @param {string} channelId - 채널 식별자 (예: "visa", "school", "main")
 * @param {Array<{role,content}>} [extraHistory] - 이 채널 대화보다 먼저 있었던 맥락
 *   (예: 메인채팅에서 넘어올 때의 대화). 화면에 표시되는 messages에는 안 섞이고,
 *   백엔드로 보내는 history 맨 앞에만 붙는다.
 * @returns {{ messages, isLoading, handleSend, suggestedChannelId, clearSuggestion }}
 *
 * suggestedChannelId: 백엔드 RAG가 답변 후 추천한 채널 ID (null이면 없음)
 * clearSuggestion:    추천 배너를 수동으로 닫을 때 호출
 */
export function useChatChannel(channelId, extraHistory = []) {
  const { getMessages, addMessage } = useApp();
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedChannelId, setSuggestedChannelId] = useState(null);

  const messages = getMessages(channelId);

  async function handleSend(text) {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    // 새 메시지 보내면 이전 추천 초기화
    setSuggestedChannelId(null);

    // 히스토리 스냅샷 — addMessage 호출 전 현재 messages 참조
    const history = [
      ...extraHistory,
      ...messages.map(m => ({ role: m.role, content: m.text })),
    ];

    addMessage(channelId, {
      id: `${channelId}-${Date.now()}-user`,
      role: 'user',
      text: trimmed,
    });

    setIsLoading(true);

    try {
      const { answer, tags, sources, suggestedChannelId: suggested, checklistId, path } =
        await sendMessage({ channelId, message: trimmed, history });

      addMessage(channelId, {
        id: `${channelId}-${Date.now()}-ai`,
        role: 'ai',
        text: answer,
        tags,
        sources,
        checklistId: checklistId ?? null,
        path: path ?? null,
      });

      // 메인채팅에서만 채널 추천을 사용 (채널 내부에서는 불필요)
      if (channelId === 'main' && suggested) {
        setSuggestedChannelId(suggested);
      }
    } finally {
      setIsLoading(false);
    }
  }

  function clearSuggestion() {
    setSuggestedChannelId(null);
  }

  return { messages, isLoading, handleSend, suggestedChannelId, clearSuggestion };
}
