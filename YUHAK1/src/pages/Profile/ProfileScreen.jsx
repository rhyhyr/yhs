import { useState, useEffect } from 'react';
import { useApp } from '../../hooks/useApp';
import { getMyProfile, getVisaInfo } from '../../api/user';
import BottomNav from '../../components/Common/BottomNav';

export default function ProfileScreen() {
  const { navigate, showToast, toggles, setToggles } = useApp();
  const [profile, setProfile] = useState(null);
  const [visa, setVisa] = useState(null);

  useEffect(() => {
    getMyProfile().then(setProfile).catch(() => {});
    getVisaInfo().then(setVisa).catch(() => {});
  }, []);

  const name       = profile?.name       ?? '—';
  const initial    = profile?.initial    ?? '?';
  const school     = profile?.school     ?? '—';
  const department = profile?.department ?? '—';
  const grade      = profile?.grade      ?? '—';
  const flag       = profile?.nationalityFlag ?? '';
  const nationality = profile?.nationality ?? '—';

  const visaType    = visa?.type        ?? '—';
  const visaLabel   = visa?.label       ?? '—';
  const expiryLabel = visa?.expiryLabel ?? '—';
  const dDay        = visa?.dDay        ?? '—';

  return (
    <>
      <div className="topbar">
        <div className="tb-title">내 정보</div>
      </div>
      <div className="scroll-area">

        {/* 프로필 헤더 — 예시 데이터 표시 */}
        <div style={{ position: 'relative' }}>
          <span className="ghost-badge" style={{ position: 'absolute', top: '12px', right: '12px', zIndex: 1 }}>예시</span>
          <div className="profile-hero" style={{ opacity: 0.55 }}>
            <div className="p-av">{initial}</div>
            <div className="p-name">{name}</div>
            <div className="p-school">{school} · {department} {grade}학년</div>
            <div className="p-badges">
              <span className="p-badge" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>🛂 {visaType} 비자</span>
              <span className="p-badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>{flag} {nationality}</span>
              <span className="p-badge" style={{ background: 'var(--c-red-l)', color: 'var(--c-red)' }}>D-{dDay}</span>
            </div>
          </div>
        </div>

        {/* 비자 정보 카드 — 예시 데이터 표시 */}
        <div style={{ position: 'relative' }}>
          <span className="ghost-badge" style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 1 }}>예시</span>
          <div className="visa-card" style={{ opacity: 0.55 }}>
            <div className="vc-hdr">🛂 비자 정보</div>
            <div className="vc-row">
              <div className="vc-label">비자 유형</div>
              <div className="vc-val">{visaLabel}</div>
            </div>
            <div className="vc-row">
              <div className="vc-label">만료일</div>
              <div className="vc-val" style={{ color: 'var(--c-red)' }}>{expiryLabel} (D-{dDay})</div>
            </div>
            <div className="vc-btn" onClick={() => showToast('비자 정보 수정 화면으로 이동합니다')}>비자 정보 수정</div>
          </div>
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
