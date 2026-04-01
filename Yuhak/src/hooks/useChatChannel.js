import { useState } from 'react';
import { useApp } from './useApp';
import { sendMessage } from '../api/chatApi';

/**
 * 채널 채팅 공통 로직 훅
 *
 * @param {string} channelId - 채널 식별자 (예: "visa", "school")
 * @returns {{ messages, isLoading, handleSend }}
 *
 * 사용 예:
 *   const { messages, isLoading, handleSend } = useChatChannel('visa');
 */
export function useChatChannel(channelId) {
  const { getMessages, addMessage } = useApp();
  const [isLoading, setIsLoading] = useState(false);

  const messages = getMessages(channelId);

  async function handleSend(text) {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    // 히스토리 스냅샷 — addMessage 호출 전 현재 messages 참조
    const history = messages.map(m => ({ role: m.role, content: m.text }));

    addMessage(channelId, {
      id: `${channelId}-${Date.now()}-user`,
      role: 'user',
      text: trimmed,
    });

    setIsLoading(true);

    try {
      const { answer } = await sendMessage({ channelId, message: trimmed, history });
      addMessage(channelId, {
        id: `${channelId}-${Date.now()}-ai`,
        role: 'ai',
        text: answer,
      });
    } finally {
      setIsLoading(false);
    }
  }

  return { messages, isLoading, handleSend };
}
