import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import { getChannel } from '../../api/channels';
import { getVisaInfo } from '../../api/user';
import { BackIcon } from '../../components/Common/icons';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';

const CHANNEL_ID = 'visa';

export default function VisaScreen() {
  const { navigate, back, infoOpen, setInfoOpen } = useApp();
  const { messages, isLoading, handleSend } = useChatChannel(CHANNEL_ID);
  const bottomRef = useRef(null);
  const [visa, setVisa] = useState(null);

  // quickActions를 channels.js 레지스트리에서 읽음
  const channel = getChannel(CHANNEL_ID);
  const quickActions = channel?.quickActions ?? [];

  useEffect(() => {
    getVisaInfo().then(setVisa).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const dDay        = visa?.dDay        ?? '87';
  const expiryLabel = visa?.expiryLabel ?? '2026. 8. 15';
  const visaType    = visa?.type        ?? 'D-2';

  function handleQuickAction(action) {
    if (action.type === 'navigate') {
      navigate(action.target);
    } else {
      handleSend(action.text);
    }
  }

  return (
    <>
      <div className="slim-header">
        <div className="tb-back" onClick={back}>
          <BackIcon />
        </div>
        <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
        <div className="slim-ch-name">비자 &amp; 체류</div>
        <div className="slim-rag">RAG 활성</div>
        <div className="slim-d87" style={{ opacity: 0.5 }} onClick={() => setInfoOpen(o => !o)}>
          <span id="d87-txt">D-{dDay}</span>
          <span id="d87-arrow" style={{ fontSize: '10px' }}>{infoOpen ? '▾' : '▸'}</span>
        </div>
      </div>

      {infoOpen && (
        <div className="info-panel" id="info-panel" style={{ opacity: 0.55 }}>
          <div className="i-chip">🗓 {visaType} 만료 <strong>{expiryLabel}</strong></div>
          <div className="i-chip green">🔔 알림 설정됨</div>
          <span className="ghost-badge" style={{ alignSelf: 'center' }}>예시</span>
        </div>
      )}

      {quickActions.length > 0 && (
        <div className="qa-scroll">
          {quickActions.map(action => (
            <button
              key={action.label}
              className="qa-btn"
              onClick={() => handleQuickAction(action)}
              disabled={isLoading}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      <div className="scroll-area">
        <div className="chat-area" id="visa-chat-area">
          {messages.length === 0 && (
            <ChatMessage role="ai">{channel?.welcomeMsg}</ChatMessage>
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
        <div style={{ height: '8px' }} />
      </div>

      <ChatInput
        inputId="visa-input"
        placeholder={channel?.placeholder ?? '비자 관련 질문하기...'}
        onSend={handleSend}
        disabled={isLoading}
      />
    </>
  );
}
