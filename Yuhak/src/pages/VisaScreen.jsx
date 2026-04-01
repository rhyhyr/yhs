import { useEffect, useRef } from 'react';
import { useApp } from '../hooks/useApp';
import { useChatChannel } from '../hooks/useChatChannel';
import { BackIcon } from '../components/icons';
import ChatInput from '../components/ChatInput';
import ChatMessage from '../components/ChatMessage';

const CHANNEL_ID = 'visa';
const WELCOME_MSG = 'D-2 채널입니다. 만료까지 87일 남았어요. 위 버튼을 탭하거나 직접 질문해주세요!';

// 퀵 액션 버튼 정의
// navigate: 다른 화면으로 이동 / question: 채팅으로 질문 전송
const QUICK_ACTIONS = [
  { label: '📋 비자 연장 절차', type: 'navigate', target: 's-step' },
  { label: '🪪 외국인등록증', type: 'question', text: '외국인등록증 재발급 절차를 알려주세요.' },
  { label: '📄 체류확인서', type: 'question', text: '체류확인서 발급 방법을 알려주세요.' },
  { label: '🔄 비자 변경', type: 'question', text: '비자 변경 절차를 알려주세요.' },
];

export default function VisaScreen() {
  const { navigate, back, infoOpen, setInfoOpen } = useApp();
  const { messages, isLoading, handleSend } = useChatChannel(CHANNEL_ID);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

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
        <div className="slim-d87" onClick={() => setInfoOpen(o => !o)}>
          <span id="d87-txt">D-87</span>
          <span id="d87-arrow" style={{ fontSize: '10px' }}>{infoOpen ? '▾' : '▸'}</span>
        </div>
      </div>

      {infoOpen && (
        <div className="info-panel" id="info-panel">
          <div className="i-chip">🗓 D-2 만료 <strong>2026. 8. 15</strong></div>
          <div className="i-chip green">🔔 알림 설정됨</div>
        </div>
      )}

      <div className="qa-scroll">
        {QUICK_ACTIONS.map(action => (
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

      <div className="scroll-area">
        <div className="chat-area" id="visa-chat-area">
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
        <div style={{ height: '8px' }} />
      </div>

      <ChatInput
        inputId="visa-input"
        placeholder="비자 관련 질문하기..."
        onSend={handleSend}
        disabled={isLoading}
      />
    </>
  );
}
