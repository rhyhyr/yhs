import { useState, useEffect, useRef } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import BottomNav from '../../components/Common/BottomNav';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';
import ChannelCreateModal from '../../components/Chat/ChannelCreateModal';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';

const CHANNEL_ID = 'main';

// 이름은 채널 레지스트리(api/channels.js)에서, 부제는 i18n chat.cat.* 에서 가져온다
const CATEGORIES = [
  { id: 'visa',   icon: '🛂', channelId: 'visa',   iconBg: 'var(--c-purple-l)' },
  { id: 'job',    icon: '💼', channelId: 'job',    iconBg: 'var(--c-amber-l)'  },
  { id: 'school', icon: '🏫', channelId: 'school', iconBg: 'var(--c-green-l)'  },
  { id: 'house',  icon: '🏠', channelId: 'house',  iconBg: 'var(--c-accent-l)' },
];

const CHANNEL_SCREEN = {
  visa:      's-visa',
  school:    's-school',
  job:       's-job',
  house:     's-house',
  insurance: 's-insurance',
};

export default function ChatScreen() {
  const { navigate, showToast, createdChannels, addCreatedChannel, toggleChannelPin } = useApp();
  const { t, localizeChannel } = useI18n();
  const catName = cat => localizeChannel(getChannel(cat.id)).name;
  const welcomeMsg = localizeChannel(getChannel(CHANNEL_ID)).welcomeMsg;
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
    showToast(t('chat.channelCreated', { name: catName(selectedCategory) }));
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
          <div className="tb-title">{localizeChannel(getChannel(CHANNEL_ID)).name}</div>
          <div className="tb-sub">{t('chat.subtitle')}</div>
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
              {cat.icon} {catName(cat)}
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
            <div className="mwc-title">{t('chat.welcomeTitle')}</div>
            <div className="mwc-desc" style={{ whiteSpace: 'pre-line' }}>
              {t('chat.welcomeDesc')}
            </div>
            <button className="mwc-btn" onClick={() => setShowWelcome(false)}>
              {t('chat.welcomeBtn')}
            </button>
          </div>
        )}

        {/* 생성된 채널 섹션 */}
        {createdChannels.length > 0 && (
          <div style={{ padding: '8px 0 4px' }}>
            <div className="sec-lbl sec-lbl--blue" style={{ paddingTop: '6px' }}>
              {t('chat.createdSection')}
            </div>
            {createdChannels.map(cat => (
              <div key={cat.id} className="ch-item" onClick={() => goToChannel(cat)}>
                <div className="ch-icon" style={{ background: cat.iconBg }}>
                  {cat.icon}
                </div>
                <div className="ch-body">
                  <div className="ch-name">{catName(cat)}</div>
                  <div className="ch-preview">{t('chat.createdPreview')}</div>
                </div>
                <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
                <button
                  className={`ch-pin-btn${cat.pinned ? ' pinned' : ''}`}
                  onClick={e => { e.stopPropagation(); toggleChannelPin(cat.id); }}
                  aria-label="pin"
                >
                  📌
                </button>
              </div>
            ))}
          </div>
        )}

        {/* 일반 채팅 영역 */}
        {!showWelcome && (
          <div className="chat-area" id="main-chat-area">
            {messages.length === 0 && (
              <ChatMessage role="ai">{welcomeMsg}</ChatMessage>
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
                <div style={{ fontSize: '20px' }}>{suggestedCat.icon}</div>
                <div className="suggestion-card-text">
                  <strong>{catName(suggestedCat)}</strong> {t('chat.viewInChannel')}<br />
                  {t(`chat.cat.${suggestedCat.id}`)}
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
          channelId={CHANNEL_ID}
          placeholder={localizeChannel(getChannel(CHANNEL_ID)).placeholder}
          onSend={handleSend}
          disabled={isLoading}
        />
      )}

      <BottomNav active="s-main" />

      {/* ── 채널 생성 확인 모달 ── */}
      {selectedCategory && (
        <ChannelCreateModal
          icon={selectedCategory.icon}
          name={catName(selectedCategory)}
          onConfirm={handleCreateChannel}
          onClose={() => setSelectedCategory(null)}
        />
      )}
    </>
  );
}
