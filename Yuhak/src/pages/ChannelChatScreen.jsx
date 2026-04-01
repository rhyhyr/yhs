import { useEffect, useRef } from 'react';
import { useApp } from '../hooks/useApp';
import { useChatChannel } from '../hooks/useChatChannel';
import { getChannel } from '../api/channels';
import { BackIcon } from '../components/icons';
import ChatInput from '../components/ChatInput';
import ChatMessage from '../components/ChatMessage';

/**
 * 채널 전용 채팅방 공통 컴포넌트
 *
 * @param {string} channelId - channels.js에 정의된 채널 ID
 *
 * 채널 메타(icon, name, welcomeMsg 등)는 channels.js에서 자동 조회.
 */
export default function ChannelChatScreen({ channelId }) {
  const { back } = useApp();
  const { messages, isLoading, handleSend } = useChatChannel(channelId);
  const bottomRef = useRef(null);

  const channel = getChannel(channelId);

  // 새 메시지 도착 시 스크롤 하단 이동
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  if (!channel) return null;

  const { icon, iconBg, name, welcomeMsg, placeholder } = channel;

  return (
    <>
      {/* 슬림 헤더 */}
      <div className="slim-header">
        <div className="tb-back" onClick={back}>
          <BackIcon />
        </div>
        <div className="slim-ch-icon" style={{ background: iconBg }}>
          {icon}
        </div>
        <div className="slim-ch-name">{name}</div>
        <div className="slim-rag">RAG 활성</div>
      </div>

      {/* 채팅 영역 */}
      <div className="scroll-area">
        <div className="chat-area" id={`${channelId}-chat-area`}>
          {/* 채팅 기록이 없을 때만 환영 메시지 표시 (히스토리에 포함되지 않음) */}
          {messages.length === 0 && (
            <ChatMessage role="ai">{welcomeMsg}</ChatMessage>
          )}
          {messages.map(msg => (
            <ChatMessage key={msg.id} role={msg.role}>
              {msg.text}
            </ChatMessage>
          ))}
          {/* 응답 대기 중 로딩 버블 */}
          {isLoading && (
            <ChatMessage role="ai">…</ChatMessage>
          )}
          <div ref={bottomRef} />
        </div>
        <div style={{ height: '8px' }} />
      </div>

      {/* 입력창 */}
      <ChatInput
        inputId={`${channelId}-input`}
        placeholder={placeholder}
        onSend={handleSend}
        disabled={isLoading}
      />
    </>
  );
}
