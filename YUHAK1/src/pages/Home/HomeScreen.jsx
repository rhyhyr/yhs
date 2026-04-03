import { useApp } from '../../hooks/useApp';
import BottomNav from '../../components/Common/BottomNav';

/* ── 고정 긴급 알림 (state 아님, 알림 성격) ── */
const URGENT_ITEMS = [
  {
    id: 'visa-expire',
    icon: '🛂',
    iconBg: 'var(--c-red-l)',
    name: '비자 만료 임박',
    preview: 'D-87 — 지금 바로 연장 서류를 준비하세요',
    time: '오늘',
    badge: { label: 'D-87', bg: 'var(--c-red-l)', color: 'var(--c-red)' },
    channelId: 'visa',
  },
];

/* ── 예시 채널 (ghost) — 실제 채널이 없을 때 흐리게 표시 ── */
const GHOST_CHANNELS = [
  { id: 'visa',      icon: '🛂', iconBg: 'var(--c-purple-l)', name: '비자 & 체류',       preview: '비자 연장, 체류기간, 외국인등록 관련 질문' },
  { id: 'school',    icon: '🏫', iconBg: 'var(--c-green-l)',  name: '학교생활',           preview: '수강신청, 학사일정, 기숙사, 장학금' },
  { id: 'job',       icon: '💼', iconBg: 'var(--c-amber-l)',  name: '취업 & 아르바이트', preview: '시간제 취업허가, 인턴십, 알바 규정' },
  { id: 'house',     icon: '🏠', iconBg: 'var(--c-accent-l)', name: '주거',               preview: '전월세 계약, 관리비, 이사 주의사항' },
  { id: 'insurance', icon: '🏥', iconBg: '#FEE2E2',           name: '병원 & 보험',        preview: '건강보험 가입, 병원 이용, 보험 혜택' },
];

/* ── 서브 컴포넌트: 일반 채널 아이템 ── */
function ChItem({ icon, iconBg, name, preview, time, badge, urgent, onClick }) {
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
    </div>
  );
}

/* ── 서브 컴포넌트: 예시(ghost) 채널 아이템 ── */
function GhostChItem({ icon, iconBg, name, preview, onClick }) {
  return (
    <div className="ch-item ghost-ch-item" onClick={onClick}>
      <div className="ch-icon" style={{ background: iconBg }}>{icon}</div>
      <div className="ch-body">
        <div className="ch-name">{name}</div>
        <div className="ch-preview">{preview}</div>
      </div>
      <div className="ch-meta">
        <span className="ghost-badge">예시</span>
      </div>
    </div>
  );
}

/* ── 메인 화면 ── */
export default function HomeScreen() {
  const { navigate, showToast, createdChannels } = useApp();

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

  return (
    <>
      {/* 상단 바 */}
      <div className="topbar">
        <div className="notif-btn" onClick={() => showToast('알림 화면은 준비 중입니다')}>
          <div style={{
            width: '34px', height: '34px', borderRadius: '10px',
            background: 'var(--c-bg)', border: '1.5px solid var(--c-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
          }}>🔔</div>
          <div className="notif-bubble">1</div>
        </div>
        <div style={{ flex: 1, marginLeft: '8px' }}>
          <div className="tb-title">UniGuide</div>
          <div className="tb-sub">안녕하세요, Wei!</div>
        </div>
        <div
          onClick={() => navigate('s-profile')}
          style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: 'var(--c-accent-l)', border: '2px solid var(--c-accent-m)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '14px', fontWeight: 700, color: 'var(--c-accent)', cursor: 'pointer',
          }}
        >W</div>
      </div>

      {/* 스크롤 본문 */}
      <div className="scroll-area">

        {/* ① 지금 확인할 것 (예시) */}
        <div className="sec-lbl sec-lbl--warn" style={{ opacity: 0.45 }}>🚨 지금 확인할 것</div>
        {URGENT_ITEMS.map(item => (
          <div key={item.id} style={{ opacity: 0.38, pointerEvents: 'auto' }}
            onClick={() => showToast('이 항목은 예시입니다')}>
            <ChItem {...item} urgent onClick={() => {}} />
          </div>
        ))}

        {/* ② 내 채널 */}
        <div className="sec-lbl" style={{ marginTop: '8px' }}>
          📂 내 채널
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
            {createdChannels.map(ch => (
              <ChItem
                key={ch.id}
                icon={ch.label.split(' ')[0]}
                iconBg={ch.iconBg}
                name={ch.label.slice(ch.label.indexOf(' ') + 1)}
                preview="탭해서 채널로 이동하세요"
                time="방금"
                badge={{ label: 'NEW', bg: 'var(--c-accent-l)', color: 'var(--c-accent)' }}
                onClick={() => goToChannel(ch)}
              />
            ))}
          </>
        ) : (
          /* 빈 상태 UI + ghost 예시 채널 */
          <>
            {/* 안내 카드 */}
            <div className="empty-channel-card">
              <div style={{ fontSize: '26px', marginBottom: '8px' }}>📭</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--c-t1)', marginBottom: '4px' }}>
                아직 생성된 채널이 없어요
              </div>
              <div style={{ fontSize: '12px', color: 'var(--c-t2)', lineHeight: 1.6, marginBottom: '14px' }}>
                메인채팅에서 궁금한 분야를 선택하면<br />채널이 생성돼요.
              </div>
              <button
                className="empty-channel-cta"
                onClick={() => navigate('s-main')}
              >
                💬 메인채팅에서 시작하기
              </button>
            </div>

            {/* 예시 채널 (ghost) */}
            <div className="sec-lbl" style={{ marginTop: '4px', color: 'var(--c-t3)' }}>
              아래는 예시입니다
            </div>
            {GHOST_CHANNELS.map(ch => (
              <GhostChItem
                key={ch.id}
                {...ch}
                onClick={() => showToast('이 채널은 예시입니다')}
              />
            ))}
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
            <div className="ch-name" style={{ color: 'var(--c-t2)' }}>새 채널 만들기</div>
            <div className="ch-preview">메인채팅에서 분야를 선택해요</div>
          </div>
        </div>

        <div style={{ height: '20px' }} />
      </div>

      <BottomNav active="s-home" />
    </>
  );
}
