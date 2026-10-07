import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import BottomNav from '../../components/Common/BottomNav';
import ChannelCreateModal from '../../components/Chat/ChannelCreateModal';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';

/* ── 고정 긴급 알림 (state 아님, 알림 성격) — 문구는 i18n home.urgent* ── */
const URGENT_ITEMS = [
  {
    id: 'visa-expire',
    icon: '🛂',
    iconBg: 'var(--c-red-l)',
    badge: { label: 'D-87', bg: 'var(--c-red-l)', color: 'var(--c-red)' },
    channelId: 'visa',
  },
];

/* ── 예시 채널 (ghost) — 실제 채널이 없을 때 흐리게 표시. 이름·아이콘은 채널 레지스트리에서 ── */
const GHOST_CHANNEL_IDS = ['visa', 'school', 'job', 'house', 'insurance'];

/* ── 서브 컴포넌트: 일반 채널 아이템 ──
   onTogglePin이 전달될 때만(=실제로 생성된 채널일 때만) 핀 버튼을 보여준다.
   예시 채널·긴급 알림 배너는 pin 대상이 아니라서 onTogglePin을 안 넘긴다. */
function ChItem({ icon, iconBg, name, preview, time, badge, urgent, pinned, onTogglePin, onClick }) {
  return (
    <div
      className={`ch-item${urgent ? ' ch-item--urgent' : ''}`}
      onClick={onClick}
    >
      <div className="ch-icon" style={{ background: iconBg }}>{icon}</div>
      <div className="ch-body">
        <div className="ch-name">{name}</div>
        <div className="ch-preview">{preview}</div>
      </div>
      <div className="ch-meta">
        <div className="ch-time">{time}</div>
        {badge && (
          <div className="badge" style={{ background: badge.bg, color: badge.color }}>
            {badge.label}
          </div>
        )}
      </div>
      {onTogglePin && (
        <button
          className={`ch-pin-btn${pinned ? ' pinned' : ''}`}
          onClick={e => { e.stopPropagation(); onTogglePin(); }}
          aria-label="pin"
        >
          📌
        </button>
      )}
    </div>
  );
}

/* ── 서브 컴포넌트: 예시(ghost) 채널 아이템 ── */
function GhostChItem({ icon, iconBg, name, preview, onClick }) {
  const { t } = useI18n();
  return (
    <div className="ch-item ghost-ch-item" onClick={onClick}>
      <div className="ch-icon" style={{ background: iconBg }}>{icon}</div>
      <div className="ch-body">
        <div className="ch-name">{name}</div>
        <div className="ch-preview">{preview}</div>
      </div>
      <div className="ch-meta">
        <span className="ghost-badge">{t('common.example')}</span>
      </div>
    </div>
  );
}

/* ── 메인 화면 ── */
export default function HomeScreen() {
  const { navigate, showToast, createdChannels, addCreatedChannel, toggleChannelPin, userProfile } = useApp();
  const { t, localizeChannel } = useI18n();

  const userName = userProfile?.name?.trim();
  const displayName = userName || t('home.greetingFallback');
  const initial = userName ? userName.charAt(0).toUpperCase() : '?';

  // 예시 채널 카드에서 "생성할까요?" 확인 중인 채널 (null이면 모달 안 뜸)
  const [selectedCategory, setSelectedCategory] = useState(null);

  // 채널 ID → 전용 화면 매핑 (채널 추가 시 여기만 수정)
  const CHANNEL_SCREEN = {
    visa:      's-visa',
    school:    's-school',
    job:       's-job',
    house:     's-house',
    insurance: 's-insurance',
  };

  function goToChannel(ch) {
    const id = ch.channelId ?? ch.id;
    const screen = CHANNEL_SCREEN[id];
    if (screen) {
      navigate(screen);
    } else {
      navigate('s-channel-chat', { channelId: id });
    }
  }

  // 예시 채널 카드 클릭 → 실제로 만들지 확인하는 모달 띄움
  // (ChatScreen의 카테고리 칩과 동일한 흐름 — addCreatedChannel 재사용)
  function handleGhostClick(id) {
    const ch = getChannel(id);
    if (!ch) return;
    setSelectedCategory({ id, channelId: id, icon: ch.icon, iconBg: ch.iconBg });
  }

  function handleCreateChannel() {
    if (!selectedCategory) return;
    addCreatedChannel(selectedCategory);
    showToast(t('chat.channelCreated', { name: localizeChannel(getChannel(selectedCategory.id)).name }));
    const cat = selectedCategory;
    setSelectedCategory(null);
    goToChannel(cat);
  }

  return (
    <>
      {/* 상단 바 */}
      <div className="topbar">
        <div className="notif-btn" onClick={() => showToast(t('home.notifSoon'))}>
          <div style={{
            width: '34px', height: '34px', borderRadius: '10px',
            background: 'var(--c-bg)', border: '1.5px solid var(--c-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
          }}>🔔</div>
          <div className="notif-bubble">1</div>
        </div>
        <div style={{ flex: 1, marginLeft: '8px' }}>
          <div className="tb-title">YuGuide</div>
          <div className="tb-sub">{t('home.greeting', { name: displayName })}</div>
        </div>
        <div
          onClick={() => navigate('s-profile')}
          style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: 'var(--c-accent-l)', border: '2px solid var(--c-accent-m)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '14px', fontWeight: 700, color: 'var(--c-accent)', cursor: 'pointer',
          }}
        >{initial}</div>
      </div>

      {/* 스크롤 본문 */}
      <div className="scroll-area">

        {/* ① 지금 확인할 것 (예시) */}
        <div className="sec-lbl sec-lbl--warn" style={{ opacity: 0.45 }}>{t('home.urgentLabel')}</div>
        {URGENT_ITEMS.map(item => (
          <div key={item.id} style={{ opacity: 0.38, pointerEvents: 'auto' }}
            onClick={() => showToast(t('home.itemIsExample'))}>
            <ChItem
              {...item}
              name={t('home.urgentTitle')}
              preview={t('home.urgentPreview')}
              time={t('time.today')}
              urgent
              onClick={() => {}}
            />
          </div>
        ))}

        {/* ② 내 채널 */}
        <div className="sec-lbl" style={{ marginTop: '8px' }}>
          {t('home.myChannels')}
          {createdChannels.length > 0 && (
            <span style={{ marginLeft: '6px', fontSize: '11px', fontWeight: 600,
              color: 'var(--c-accent)', background: 'var(--c-accent-l)',
              padding: '1px 7px', borderRadius: '8px' }}>
              {createdChannels.length}
            </span>
          )}
        </div>

        {createdChannels.length > 0 ? (
          /* 생성된 채널 목록 */
          <>
            {createdChannels.map(ch => {
              const info = localizeChannel(getChannel(ch.id));
              return (
                <ChItem
                  key={ch.id}
                  icon={info?.icon ?? ch.icon}
                  iconBg={ch.iconBg}
                  name={info?.name ?? ch.id}
                  preview={t('home.tapToOpen')}
                  time={t('time.justNow')}
                  badge={{ label: 'NEW', bg: 'var(--c-accent-l)', color: 'var(--c-accent)' }}
                  pinned={ch.pinned}
                  onTogglePin={() => toggleChannelPin(ch.id)}
                  onClick={() => goToChannel(ch)}
                />
              );
            })}
          </>
        ) : (
          /* 빈 상태 UI + ghost 예시 채널 */
          <>
            {/* 안내 카드 */}
            <div className="empty-channel-card">
              <div style={{ fontSize: '26px', marginBottom: '8px' }}>📭</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--c-t1)', marginBottom: '4px' }}>
                {t('home.emptyTitle')}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--c-t2)', lineHeight: 1.6, marginBottom: '14px', whiteSpace: 'pre-line' }}>
                {t('home.emptyDesc')}
              </div>
              <button
                className="empty-channel-cta"
                onClick={() => navigate('s-main')}
              >
                {t('home.startInMain')}
              </button>
            </div>

            {/* 예시 채널 (ghost) */}
            <div className="sec-lbl" style={{ marginTop: '4px', color: 'var(--c-t3)' }}>
              {t('home.belowAreExamples')}
            </div>
            {GHOST_CHANNEL_IDS.map(id => {
              const ch = localizeChannel(getChannel(id));
              return (
                <GhostChItem
                  key={id}
                  icon={ch.icon}
                  iconBg={ch.iconBg}
                  name={ch.name}
                  preview={t(`home.ghost.${id}`)}
                  onClick={() => handleGhostClick(id)}
                />
              );
            })}
          </>
        )}

        {/* ③ 채널 추가 버튼 */}
        <div
          className="ch-item"
          onClick={() => navigate('s-main')}
          style={{ marginTop: '4px' }}
        >
          <div className="ch-icon" style={{
            background: 'var(--c-bg)',
            border: '1.5px dashed var(--c-border-s)',
            fontSize: '22px',
          }}>+</div>
          <div className="ch-body">
            <div className="ch-name" style={{ color: 'var(--c-t2)' }}>{t('home.newChannel')}</div>
            <div className="ch-preview">{t('home.newChannelSub')}</div>
          </div>
        </div>

        <div style={{ height: '20px' }} />
      </div>

      <BottomNav active="s-home" />

      {selectedCategory && (
        <ChannelCreateModal
          icon={selectedCategory.icon}
          name={localizeChannel(getChannel(selectedCategory.id)).name}
          onConfirm={handleCreateChannel}
          onClose={() => setSelectedCategory(null)}
        />
      )}
    </>
  );
}
