import { useApp } from '../hooks/useApp';
import BottomNav from '../components/BottomNav';

/* ── 데이터 ── */
const URGENT_ITEMS = [
  {
    id: 'visa-expire',
    icon: '🛂',
    iconBg: 'var(--c-red-l)',
    name: '비자 만료 임박',
    preview: 'D-87 — 지금 바로 연장 서류를 준비하세요',
    time: '오늘',
    badge: { label: 'D-87', bg: 'var(--c-red-l)', color: 'var(--c-red)' },
    onClick: (nav) => nav('s-visa'),
  },
  {
    id: 'new-reply',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    name: '취업 & 아르바이트',
    preview: '시간제 취업 허가 절차 — 새 답변이 도착했습니다',
    time: '방금',
    badge: { label: '새 답변', bg: 'var(--c-accent-l)', color: 'var(--c-accent)' },
    onClick: (nav) => nav('s-job'),
  },
];

const RECENT_CHATS = [
  {
    id: 'visa-chat',
    icon: '🛂',
    iconBg: 'var(--c-purple-l)',
    name: '비자 & 체류',
    preview: '비자 연장하려면 뭐가 필요해요?',
    time: '방금',
    badge: null,
    onClick: (nav) => nav('s-visa'),
  },
  {
    id: 'school',
    icon: '🏫',
    iconBg: 'var(--c-green-l)',
    name: '학교생활',
    preview: '수강신청은 어떻게 하나요?',
    time: '어제',
    badge: null,
    onClick: (nav) => nav('s-school'),
  },
  {
    id: 'job',
    icon: '💼',
    iconBg: 'var(--c-amber-l)',
    name: '취업 & 아르바이트',
    preview: '시간제 취업 허가 절차 안내 완료',
    time: '3일 전',
    badge: { label: '새 답변', bg: 'var(--c-accent-l)', color: 'var(--c-accent)' },
    onClick: (nav) => nav('s-job'),
  },
];

const ALL_CHANNELS = [
  {
    id: 'housing',
    icon: '🏠',
    iconBg: 'var(--c-accent-l)',
    name: '주거',
    preview: '계약 만료 60일 전 알림 설정됨',
    time: '1주 전',
    onClick: (nav) => nav('s-house'),
  },
  {
    id: 'medical',
    icon: '🏥',
    iconBg: '#FEE2E2',
    name: '병원 & 보험',
    preview: '건강보험 가입 완료',
    time: '2주 전',
    onClick: (nav) => nav('s-insurance'),
  },
];

/* ── 서브 컴포넌트 ── */
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

/* ── 메인 화면 ── */
export default function HomeScreen() {
  const { navigate, showToast } = useApp();

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
          <div className="notif-bubble">2</div>
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

        {/* ① 지금 확인할 것 */}
        <div className="sec-lbl sec-lbl--warn">🚨 지금 확인할 것</div>
        {URGENT_ITEMS.map(item => (
          <ChItem key={item.id} {...item} urgent onClick={() => item.onClick(navigate)} />
        ))}

        {/* ② 최근 대화 */}
        <div className="sec-lbl sec-lbl--blue" style={{ marginTop: '8px' }}>💬 최근 대화</div>
        {RECENT_CHATS.map(item => (
          <ChItem key={item.id} {...item} onClick={() => item.onClick(navigate)} />
        ))}

        {/* ③ 전체 채널 */}
        <div className="sec-lbl" style={{ marginTop: '8px' }}>전체 채널</div>
        {ALL_CHANNELS.map(item => (
          <ChItem key={item.id} {...item} onClick={() => item.onClick(navigate)} />
        ))}

        {/* 채널 추가 */}
        <div
          className="ch-item"
          onClick={() => showToast('채널 생성 화면으로 이동합니다')}
        >
          <div className="ch-icon" style={{
            background: 'var(--c-bg)',
            border: '1.5px dashed var(--c-border-s)',
            fontSize: '22px',
          }}>+</div>
          <div className="ch-body">
            <div className="ch-name" style={{ color: 'var(--c-t2)' }}>새 채널 만들기</div>
            <div className="ch-preview">생활정보, 커뮤니티 등</div>
          </div>
        </div>

        <div style={{ height: '20px' }} />
      </div>

      <BottomNav active="s-home" />
    </>
  );
}
