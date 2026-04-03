import { useState, useEffect, useRef } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import BottomNav from '../../components/Common/BottomNav';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';

const CHANNEL_ID = 'main';
const WELCOME_MSG = '안녕하세요! 무엇이든 질문하세요. 적합한 채널로 안내해 드리겠습니다.';

const CATEGORIES = [
  { id: 'visa',   label: '🛂 비자 & 체류',       channelId: 'visa',   iconBg: 'var(--c-purple-l)' },
  { id: 'job',    label: '💼 취업 & 아르바이트', channelId: 'job',    iconBg: 'var(--c-amber-l)'  },
  { id: 'school', label: '🏫 학교생활',           channelId: 'school', iconBg: 'var(--c-green-l)'  },
  { id: 'house',  label: '🏠 주거',               channelId: 'house',  iconBg: 'var(--c-accent-l)' },
];

const CHANNEL_SCREEN = {
  visa:      's-visa',
  school:    's-school',
  job:       's-job',
  house:     's-house',
  insurance: 's-insurance',
};

export default function ChatScreen() {
  const { navigate, showToast, createdChannels, addCreatedChannel } = useApp();
  const { messages, isLoading, handleSend, suggestedChannelId, clearSuggestion } =
    useChatChannel(CHANNEL_ID);
  const bottomRef = useRef(null);

  const [showWelcome, setShowWelcome] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // 추천 채널 카테고리 객체
  const suggestedCat = suggestedChannelId
    ? CATEGORIES.find(c => c.id === suggestedChannelId)
    : null;

  function handleCategoryClick(cat) {
    if (createdChannels.find(c => c.id === cat.id)) {
      goToChannel(cat);
      return;
    }
    setSelectedCategory(cat);
  }

  function handleCreateChannel() {
    if (!selectedCategory) return;
    addCreatedChannel(selectedCategory);
    showToast(`${selectedCategory.label} 채널이 생성되었어요 🎉`);
    const cat = selectedCategory;
    setSelectedCategory(null);
    clearSuggestion();
    goToChannel(cat);
  }

  // 채널 이동 시 메인채팅 대화 맥락을 initialHistory로 전달
  function goToChannel(cat) {
    const screen = CHANNEL_SCREEN[cat.channelId];
    const initialHistory = messages.map(m => ({ role: m.role, content: m.text }));
    if (screen) {
      navigate(screen, { initialHistory });
    } else {
      navigate('s-channel-chat', { channelId: cat.channelId, initialHistory });
    }
  }

  return (
    <>
      {/* ── 상단 바 ── */}
      <div className="topbar">
        <div>
          <div className="tb-title">메인 채팅</div>
          <div className="tb-sub">모든 채널에 질문하기</div>
        </div>
      </div>

      {/* ── 카테고리 단축칩 ── */}
      <div className="qa-scroll">
        {CATEGORIES.map(cat => {
          const isCreated   = createdChannels.find(c => c.id === cat.id);
          const isSuggested = suggestedChannelId === cat.id;
          let chipClass = 'main-shortcut-chip';
          if (isCreated)   chipClass += ' created';
          if (isSuggested) chipClass += ' suggested';
          return (
            <button
              key={cat.id}
              className={chipClass}
              onClick={() => handleCategoryClick(cat)}
            >
              {cat.label}
              {isCreated   && <span className="chip-dot" />}
              {isSuggested && <span className="chip-dot suggested-dot" />}
            </button>
          );
        })}
      </div>

      {/* ── 스크롤 본문 ── */}
      <div className="scroll-area">

        {/* 웰컴 카드 */}
        {showWelcome && (
          <div className="main-welcome-card">
            <div className="mwc-emoji">✨</div>
            <div className="mwc-title">무엇이 궁금해서 오셨나요?</div>
            <div className="mwc-desc">
              비자, 학교, 주거, 아르바이트처럼<br />
              궁금한 주제를 골라 바로 시작할 수 있어요.
            </div>
            <button className="mwc-btn" onClick={() => setShowWelcome(false)}>
              💬 메인채팅으로 가기
            </button>
          </div>
        )}

        {/* 생성된 채널 섹션 */}
        {createdChannels.length > 0 && (
          <div style={{ padding: '8px 0 4px' }}>
            <div className="sec-lbl sec-lbl--blue" style={{ paddingTop: '6px' }}>
              ✅ 방금 생성된 채널
            </div>
            {createdChannels.map(cat => (
              <div key={cat.id} className="ch-item" onClick={() => goToChannel(cat)}>
                <div className="ch-icon" style={{ background: cat.iconBg }}>
                  {cat.label.split(' ')[0]}
                </div>
                <div className="ch-body">
                  <div className="ch-name">{cat.label.slice(cat.label.indexOf(' ') + 1)}</div>
                  <div className="ch-preview">전문 채널에서 더 자세한 답변을 받아보세요</div>
                </div>
                <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
              </div>
            ))}
          </div>
        )}

        {/* 일반 채팅 영역 */}
        {!showWelcome && (
          <div className="chat-area" id="main-chat-area">
            {messages.length === 0 && (
              <ChatMessage role="ai">{WELCOME_MSG}</ChatMessage>
            )}
            {messages.map(msg => (
              <ChatMessage key={msg.id} role={msg.role}>
                {msg.text}
              </ChatMessage>
            ))}
            {isLoading && <ChatMessage role="ai">…</ChatMessage>}

            {/* 채널 추천 카드 — 백엔드 suggestedChannelId 수신 시 표시 */}
            {suggestedCat && !isLoading && (
              <div
                className="suggestion-card"
                onClick={() => handleCategoryClick(suggestedCat)}
              >
                <div style={{ fontSize: '20px' }}>{suggestedCat.label.split(' ')[0]}</div>
                <div className="suggestion-card-text">
                  <strong>{suggestedCat.label.slice(suggestedCat.label.indexOf(' ') + 1)}</strong> 채널에서<br />
                  더 정확한 답변을 받아보세요
                </div>
                <div className="suggestion-card-arrow">›</div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}

        <div style={{ height: '16px' }} />
      </div>

      {/* ── 채팅 입력 ── */}
      {!showWelcome && (
        <ChatInput
          inputId="main-input"
          placeholder="무엇이든 질문하세요..."
          onSend={handleSend}
          disabled={isLoading}
        />
      )}

      <BottomNav active="s-main" />

      {/* ── 채널 생성 확인 모달 ── */}
      {selectedCategory && (
        <div className="source-modal-overlay" onClick={() => setSelectedCategory(null)}>
          <div className="channel-modal-sheet" onClick={e => e.stopPropagation()}>
            <div className="source-modal-handle" />
            <div style={{ textAlign: 'center', padding: '4px 0 8px' }}>
              <div style={{ fontSize: '36px', marginBottom: '10px' }}>
                {selectedCategory.label.split(' ')[0]}
              </div>
              <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--c-t1)', marginBottom: '6px' }}>
                {selectedCategory.label.slice(selectedCategory.label.indexOf(' ') + 1)} 채널을 생성할까요?
              </div>
              <div style={{ fontSize: '13px', color: 'var(--c-t2)', lineHeight: 1.6 }}>
                더 자세하고 전문적인 답변을<br />받아보실 수 있어요.
              </div>
            </div>
            <button className="channel-modal-btn primary" onClick={handleCreateChannel}>
              채널 생성하기
            </button>
            <button className="channel-modal-btn secondary" onClick={() => setSelectedCategory(null)}>
              나중에
            </button>
          </div>
        </div>
      )}
    </>
  );
}
