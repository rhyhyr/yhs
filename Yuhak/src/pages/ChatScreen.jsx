import { useEffect, useRef } from 'react';
import { useChatChannel } from '../hooks/useChatChannel';
import BottomNav from '../components/BottomNav';
import ChatInput from '../components/ChatInput';
import ChatMessage from '../components/ChatMessage';

const CHANNEL_ID = 'main';
const WELCOME_MSG = '안녕하세요! 무엇이든 질문하세요. 적합한 채널로 안내해 드리겠습니다.';

export default function ChatScreen() {
  const { messages, isLoading, handleSend } = useChatChannel(CHANNEL_ID);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <>
      <div className="topbar">
        <div>
          <div className="tb-title">메인 채팅</div>
          <div className="tb-sub">모든 채널에 질문하기</div>
        </div>
      </div>

      <div className="scroll-area">
        <div className="chat-area" id="main-chat-area">
          {messages.length === 0 && (
            <ChatMessage role="ai">{WELCOME_MSG}</ChatMessage>
          )}
          {messages.map(msg => (
            <ChatMessage key={msg.id} role={msg.role}>
              {msg.text}
            </ChatMessage>
          ))}
          {isLoading && (
            <ChatMessage role="ai">…</ChatMessage>
          )}
          <div ref={bottomRef} />
        </div>
        <div style={{ height: '16px' }} />
      </div>

      <ChatInput
        inputId="main-input"
        placeholder="무엇이든 질문하세요..."
        onSend={handleSend}
        disabled={isLoading}
      />
      <BottomNav active="s-main" />
    </>
  );
}
