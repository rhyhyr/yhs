import { useState, useEffect, useRef } from 'react';
import { useApp } from '../../hooks/useApp';
import { getChannelById } from '../../data/channels';
import { getChannelMessages, sendMessage, createMessage } from '../../api/chat';
import { BackIcon } from '../../components/Common/icons';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';

/**
 * 채널 전용 채팅방 공통 컴포넌트
 *
 * - props.channelId 로 어떤 채널인지 결정
 * - 채널 메타(헤더·placeholder·welcomeMsg)는 data/channels.js에서 조회
 * - 메시지 송수신은 api/chat.js (mock → fetch 교체 가능)
 * - 메시지 state는 이 컴포넌트가 로컬로 관리 (화면별 독립)
 */
export default function ChannelChatScreen({ channelId }) {
  const { back, navParams } = useApp();
  const channel = getChannelById(channelId);

  const [messages, setMessages]   = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  // 메인채팅에서 넘어온 대화 맥락 — 채널 RAG에 컨텍스트 제공
  // useRef로 캡처하여 최초 진입 시점의 history만 사용
  const initialHistoryRef = useRef(navParams?.initialHistory ?? []);

  // 진입 시 이전 메시지 불러오기
  // mock 단계에서는 빈 배열 반환, 실제 API 연결 후 히스토리 복원
  useEffect(() => {
    let cancelled = false;
    getChannelMessages(channelId)
      .then(msgs => { if (!cancelled) setMessages(msgs); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [channelId]);

  // 새 메시지 도착 시 스크롤 하단 이동
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  async function handleSend(text) {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    // 히스토리 스냅샷 — 메인채팅 맥락(initialHistory) + 현재 채널 대화
    const history = [
      ...initialHistoryRef.current,
      ...messages.map(m => ({ role: m.role, content: m.text })),
    ];

    // 사용자 메시지 즉시 추가
    const userMsg = createMessage({ channelId, role: 'user', text: trimmed });
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const { answer, sources } = await sendMessage({ channelId, message: trimmed, history });
      const aiMsg = createMessage({ channelId, role: 'ai', text: answer, sources });
      setMessages(prev => [...prev, aiMsg]);
    } catch {
      const errMsg = createMessage({
        channelId,
        role: 'ai',
        text: '응답을 불러오는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.',
      });
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  }

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
          {/* 대화 기록 없을 때 환영 메시지 */}
          {messages.length === 0 && !isLoading && (
            <ChatMessage role="ai">{welcomeMsg}</ChatMessage>
          )}
          {messages.map(msg => (
            <ChatMessage key={msg.id} role={msg.role}>
              {msg.text}
            </ChatMessage>
          ))}
          {isLoading && <ChatMessage role="ai">…</ChatMessage>}
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
