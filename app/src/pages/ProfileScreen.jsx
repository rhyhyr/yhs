import { useApp } from '../hooks/useApp';
import BottomNav from '../components/BottomNav';

export default function ProfileScreen() {
  const { navigate, showToast, toggles, setToggles } = useApp();
  return (
    <>
      <div className="topbar">
        <div className="tb-title">내 정보</div>
      </div>
      <div className="scroll-area">
        <div className="profile-hero">
          <div className="p-av">W</div>
          <div className="p-name">Wei Zhang</div>
          <div className="p-school">부산대학교 · 컴퓨터공학과 3학년</div>
          <div className="p-badges">
            <span className="p-badge" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>🛂 D-2 비자</span>
            <span className="p-badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>🇨🇳 중국</span>
            <span className="p-badge" style={{ background: 'var(--c-red-l)', color: 'var(--c-red)' }}>D-87</span>
          </div>
        </div>
        <div className="visa-card">
          <div className="vc-hdr">🛂 비자 정보</div>
          <div className="vc-row">
            <div className="vc-label">비자 유형</div>
            <div className="vc-val">D-2 (학생)</div>
          </div>
          <div className="vc-row">
            <div className="vc-label">만료일</div>
            <div className="vc-val" style={{ color: 'var(--c-red)' }}>2026. 8. 15 (D-87)</div>
          </div>
          <div className="vc-btn" onClick={() => showToast('비자 정보 수정 화면으로 이동합니다')}>비자 정보 수정</div>
        </div>
        <div className="setting-sec">알림 설정</div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
          <div className="s-body">
            <div className="s-name">비자 &amp; 체류 알림</div>
            <div className="s-val">만료 90일·30일·7일 전</div>
          </div>
          <div className={`toggle-track ${toggles.visa ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, visa: !t.visa })); showToast(toggles.visa ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-amber-l)' }}>🏠</div>
          <div className="s-body">
            <div className="s-name">주거 계약 알림</div>
            <div className="s-val">만료 60일 전</div>
          </div>
          <div className={`toggle-track ${toggles.house ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, house: !t.house })); showToast(toggles.house ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-green-l)' }}>🏥</div>
          <div className="s-body">
            <div className="s-name">보험료 납부 알림</div>
            <div className="s-val">납부일 5일 전</div>
          </div>
          <div className={`toggle-track ${toggles.insurance ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, insurance: !t.insurance })); showToast(toggles.insurance ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-sec">앱 설정</div>
        <div className="setting-row" onClick={() => showToast('언어 설정 화면으로 이동합니다')}>
          <div className="s-icon" style={{ background: 'var(--c-accent-l)' }}>🌐</div>
          <div className="s-body">
            <div className="s-name">사용 언어</div>
            <div className="s-val">한국어 · 中文</div>
          </div>
          <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
        </div>
        <div className="setting-row" onClick={() => showToast('개인정보 수정 화면으로 이동합니다')}>
          <div className="s-icon" style={{ background: 'var(--c-bg)' }}>👤</div>
          <div className="s-body">
            <div className="s-name">개인정보 수정</div>
            <div className="s-val">이름, 학교, 학과</div>
          </div>
          <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
        </div>
        <div className="logout-btn" onClick={() => navigate('s-onboarding')}>로그아웃</div>
        <div style={{ height: '20px' }} />
      </div>
      <BottomNav active="s-profile" />
    </>
  );
}
