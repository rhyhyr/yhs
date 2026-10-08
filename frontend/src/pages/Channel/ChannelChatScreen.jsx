import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import { getChannelById } from '../../data/channels';
import { BackIcon } from '../../components/Common/icons';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';
import { useI18n } from '../../i18n';

/**
 * 채널 전용 채팅방 공통 컴포넌트 (취업/주거/보험 등)
 *
 * - props.channelId 로 어떤 채널인지 결정
 * - 채널 메타(헤더·placeholder·welcomeMsg)는 data/channels.js에서 조회
 * - 메시지는 useChatChannel(공유 훅)을 통해 AppContext의 chatState에 저장된다
 *   — Visa/SchoolScreen과 같은 방식이라, 화면을 나갔다 와도 대화가 안 사라지고
 *   "기록" 탭(answerHistory)에도 같이 잡힌다.
 */
export default function ChannelChatScreen({ channelId }) {
  const { back, navigate, navParams, setDraft } = useApp();
  const { t, localizeChannel } = useI18n();
  const channel = localizeChannel(getChannelById(channelId));

  // 메인채팅에서 넘어온 대화 맥락 — 채널 RAG에 컨텍스트로만 제공 (화면엔 안 보임)
  // useState lazy init으로 마운트 시점 값만 한 번 캡처 (렌더 중 ref.current 직접 읽기 방지)
  const [initialHistory] = useState(() => navParams?.initialHistory ?? []);
  const { messages, isLoading, handleSend } = useChatChannel(channelId, initialHistory);
  const bottomRef = useRef(null);

  // 새 메시지 도착 시 스크롤 하단 이동
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // ── "관련 대화 보기"(캘린더·검색 기록)로 돌아왔을 때 해당 메시지로 스크롤 ──
  // 채팅 기록은 새로고침하면 사라지는 구조라, 못 찾으면 조용히 그냥 둔다.
  const highlightMessageId = navParams?.highlightMessageId ?? null;
  const [highlightedId, setHighlightedId] = useState(null);
  const msgRefs = useRef({});
  useEffect(() => {
    if (!highlightMessageId) return;
    const el = msgRefs.current[highlightMessageId];
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setHighlightedId(highlightMessageId);
    const timer = setTimeout(() => setHighlightedId(null), 2000);
    return () => clearTimeout(timer);
  }, [highlightMessageId]);

  if (!channel) return null;

  const { icon, iconBg, name, welcomeMsg, placeholder, quickActions = [] } = channel;

  // 질문형 버튼은 바로 전송하지 않고 입력창에 채워서, 사용자가 확인/수정 후 직접 전송하게 함
  function handleQuickAction(action) {
    if (action.type === 'navigate') navigate(action.target);
    else setDraft(channelId, action.text);
  }

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
        <div className="slim-rag">{t('common.ragActive')}</div>
      </div>

      {/* 추천 질문 버튼 — 채널 데이터(data/channels.js)의 quickActions 기준 */}
      {quickActions.length > 0 && (
        <div className="qa-scroll">
          {quickActions.map(action => (
            <button key={action.label} className={`qa-btn${action.example ? ' qa-btn-example' : ''}`}
              onClick={() => handleQuickAction(action)} disabled={isLoading}>
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* 채팅 영역 */}
      <div className="scroll-area">
        <div className="chat-area" id={`${channelId}-chat-area`}>
          {/* 대화 기록 없을 때 환영 메시지 */}
          {messages.length === 0 && !isLoading && (
            <ChatMessage role="ai">{welcomeMsg}</ChatMessage>
          )}
          {messages.map(msg => (
            <div
              key={msg.id}
              ref={el => { msgRefs.current[msg.id] = el; }}
              className={highlightedId === msg.id ? 'msg-highlighted' : ''}
            >
              <ChatMessage role={msg.role}>{msg.text}</ChatMessage>
            </div>
          ))}
          {isLoading && <ChatMessage role="ai">…</ChatMessage>}
          <div ref={bottomRef} />
        </div>
        <div style={{ height: '8px' }} />
      </div>

      {/* 입력창 */}
      <ChatInput
        inputId={`${channelId}-input`}
        channelId={channelId}
        placeholder={placeholder}
        onSend={handleSend}
        disabled={isLoading}
      />
    </>
  );
}
