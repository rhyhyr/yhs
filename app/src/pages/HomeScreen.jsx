import { useApp } from '../hooks/useApp';
import BottomNav from '../components/BottomNav';

export default function HomeScreen() {
  const { navigate, showToast } = useApp();
  return (
    <>
      <div className="topbar">
        <div className="notif-btn" onClick={() => navigate('notif-placeholder')}>
          <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: 'var(--c-bg)', border: '1.5px solid var(--c-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' }}>🔔</div>
          <div className="notif-bubble">2</div>
        </div>
        <div style={{ flex: 1, marginLeft: '8px' }}>
          <div className="tb-title">UniGuide</div>
          <div className="tb-sub">안녕하세요, Wei!</div>
        </div>
        <div onClick={() => navigate('s-profile')} style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--c-accent-l)', border: '2px solid var(--c-accent-m)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 700, color: 'var(--c-accent)', cursor: 'pointer' }}>W</div>
      </div>
      <div className="info-chip urgent">
        🛂 D-2 비자 만료까지 <strong>87일</strong> 남았습니다
      </div>
      <div className="scroll-area">
        <div className="sec-lbl">내 채널</div>
        <div className="ch-item" onClick={() => navigate('s-visa')}>
          <div className="ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
          <div className="ch-body">
            <div className="ch-name">비자 &amp; 체류</div>
            <div className="ch-preview">비자 연장하려면 뭐가 필요해요?</div>
          </div>
          <div className="ch-meta">
            <div className="ch-time">방금</div>
            <div className="badge" style={{ background: 'var(--c-red-l)', color: 'var(--c-red)' }}>D-87</div>
          </div>
        </div>
        <div className="ch-item" onClick={() => navigate('s-main')}>
          <div className="ch-icon" style={{ background: 'var(--c-green-l)' }}>🏫</div>
          <div className="ch-body">
            <div className="ch-name">학교생활</div>
            <div className="ch-preview">수강신청은 어떻게 하나요?</div>
          </div>
          <div className="ch-meta"><div className="ch-time">어제</div></div>
        </div>
        <div className="ch-item" onClick={() => navigate('s-main')}>
          <div className="ch-icon" style={{ background: 'var(--c-amber-l)' }}>💼</div>
          <div className="ch-body">
            <div className="ch-name">취업 &amp; 아르바이트</div>
            <div className="ch-preview">시간제 취업 허가 절차 안내 완료</div>
          </div>
          <div className="ch-meta">
            <div className="ch-time">3일 전</div>
            <div className="badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>새 답변</div>
          </div>
        </div>
        <div className="ch-item" onClick={() => navigate('s-main')}>
          <div className="ch-icon" style={{ background: 'var(--c-accent-l)' }}>🏠</div>
          <div className="ch-body">
            <div className="ch-name">주거</div>
            <div className="ch-preview">계약 만료 60일 전 알림 설정됨</div>
          </div>
          <div className="ch-meta"><div className="ch-time">1주 전</div></div>
        </div>
        <div className="ch-item" onClick={() => navigate('s-main')}>
          <div className="ch-icon" style={{ background: '#FEE2E2' }}>🏥</div>
          <div className="ch-body">
            <div className="ch-name">병원 &amp; 보험</div>
            <div className="ch-preview">건강보험 가입 완료</div>
          </div>
          <div className="ch-meta"><div className="ch-time">2주 전</div></div>
        </div>
        <div className="sec-lbl">채널 추가</div>
        <div className="ch-item" onClick={() => showToast('채널 생성 화면으로 이동합니다')}>
          <div className="ch-icon" style={{ background: 'var(--c-bg)', border: '1.5px dashed var(--c-border-s)', fontSize: '22px' }}>+</div>
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
