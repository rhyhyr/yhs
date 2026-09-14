import { useApp } from '../../hooks/useApp';
import BottomNav from '../../components/Common/BottomNav';

function getInitial(name) {
  const trimmed = name?.trim();
  return trimmed ? trimmed.charAt(0).toUpperCase() : '?';
}

function formatSchoolLine(school, department, grade) {
  if (!school) return '학교 정보 없음';
  const parts = [school];
  if (department) parts.push(department);
  if (grade) parts.push(`${grade}학년`);
  return parts.join(' · ');
}

export default function ProfileScreen() {
  const { navigate, showToast, toggles, setToggles, userProfile } = useApp();

  const name         = userProfile?.name       || '이름 없음';
  const initial      = getInitial(userProfile?.name);
  const schoolLine   = formatSchoolLine(userProfile?.school, userProfile?.department, userProfile?.grade);
  const nationality  = userProfile?.nationality || '—';
  const visaType     = userProfile?.visaType    || '—';

  return (
    <>
      <div className="topbar">
        <div className="tb-title">내 정보</div>
      </div>
      <div className="scroll-area">

        {/* 프로필 헤더 */}
        <div className="profile-hero">
          <div className="p-av">{initial}</div>
          <div className="p-name">{name}</div>
          <div className="p-school">{schoolLine}</div>
          <div className="p-badges">
            {visaType !== '—' && (
              <span className="p-badge" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>
                🛂 {visaType}
              </span>
            )}
            {nationality !== '—' && (
              <span className="p-badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>
                {nationality}
              </span>
            )}
          </div>
        </div>

        {/* 비자 정보 카드 */}
        <div className="visa-card">
          <div className="vc-hdr">🛂 비자 정보</div>
          <div className="vc-row">
            <div className="vc-label">비자 유형</div>
            <div className="vc-val">{visaType}</div>
          </div>
          <div className="vc-row">
            <div className="vc-label">만료일</div>
            <div className="vc-val" style={{ color: 'var(--c-red)' }}>비자 채널에서 입력해주세요</div>
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
            <div className="s-val">
              {userProfile?.languages?.length
                ? userProfile.languages.map(l => ({ ko: '한국어', zh: '中文', en: 'English', vi: 'Tiếng Việt' }[l] ?? l)).join(' · ')
                : '—'}
            </div>
          </div>
          <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
        </div>
        <div className="setting-row" onClick={() => navigate('s-onboarding')}>
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
