import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { visaTypeKey } from '../../data/visaTypes';
import BottomNav from '../../components/Common/BottomNav';

function getInitial(name) {
  const trimmed = name?.trim();
  return trimmed ? trimmed.charAt(0).toUpperCase() : '?';
}

export default function ProfileScreen() {
  const {
    navigate, showToast, toggles, setToggles, userProfile, updateUserProfile,
    googleAccessToken, googleConnecting, connectGoogleCalendar, disconnectGoogleCalendar,
  } = useApp();
  const { t, locale, setLocale, languages } = useI18n();
  const [langOpen, setLangOpen] = useState(false);

  function formatSchoolLine(school, department, grade) {
    if (!school) return t('profile.noSchool');
    const parts = [school];
    if (department) parts.push(department);
    if (grade) parts.push(t('common.gradeN', { n: grade }));
    return parts.join(' · ');
  }

  // 비자 유형은 저장된 값(예: 'D-2 학생')을 현재 언어의 이름으로 바꿔서 보여준다
  const rawVisaType  = userProfile?.visaType;
  const visaTypeName = rawVisaType
    ? (visaTypeKey(rawVisaType) ? t(`visaTypes.${visaTypeKey(rawVisaType)}`) : rawVisaType)
    : '—';

  const name         = userProfile?.name       || t('profile.noName');
  const initial      = getInitial(userProfile?.name);
  const schoolLine   = formatSchoolLine(userProfile?.school, userProfile?.department, userProfile?.grade);
  const nationality  = userProfile?.nationality || '—';
  const visaType     = visaTypeName;

  function toggleNotif(key) {
    setToggles(prev => ({ ...prev, [key]: !prev[key] }));
    showToast(toggles[key] ? t('profile.notifOff') : t('profile.notifOn'));
  }

  function chooseLanguage(code) {
    setLocale(code);
    updateUserProfile({ languages: [code] });
    setLangOpen(false);
  }

  function handleGoogleRowClick() {
    if (googleConnecting) return;
    if (googleAccessToken) disconnectGoogleCalendar();
    else connectGoogleCalendar();
  }

  const currentLang = languages.find(l => l.code === locale);

  return (
    <>
      <div className="topbar">
        <div className="tb-title">{t('profile.title')}</div>
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
          <div className="vc-hdr">{t('profile.visaInfo')}</div>
          <div className="vc-row">
            <div className="vc-label">{t('profile.visaType')}</div>
            <div className="vc-val">{visaType}</div>
          </div>
          <div className="vc-row">
            <div className="vc-label">{t('profile.expiry')}</div>
            <div className="vc-val" style={{ color: 'var(--c-red)' }}>{t('profile.expiryHint')}</div>
          </div>
          <div className="vc-btn" onClick={() => showToast(t('profile.editVisaToast'))}>{t('profile.editVisa')}</div>
        </div>

        <div className="setting-sec">{t('profile.notifSection')}</div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
          <div className="s-body">
            <div className="s-name">{t('profile.visaNotif')}</div>
            <div className="s-val">{t('profile.visaNotifSub')}</div>
          </div>
          <div className={`toggle-track ${toggles.visa ? 'on' : 'off'}`} onClick={() => toggleNotif('visa')}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-amber-l)' }}>🏠</div>
          <div className="s-body">
            <div className="s-name">{t('profile.houseNotif')}</div>
            <div className="s-val">{t('profile.houseNotifSub')}</div>
          </div>
          <div className={`toggle-track ${toggles.house ? 'on' : 'off'}`} onClick={() => toggleNotif('house')}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-row">
          <div className="s-icon" style={{ background: 'var(--c-green-l)' }}>🏥</div>
          <div className="s-body">
            <div className="s-name">{t('profile.insNotif')}</div>
            <div className="s-val">{t('profile.insNotifSub')}</div>
          </div>
          <div className={`toggle-track ${toggles.insurance ? 'on' : 'off'}`} onClick={() => toggleNotif('insurance')}>
            <div className="toggle-knob" />
          </div>
        </div>

        <div className="setting-sec">{t('profile.appSection')}</div>
        <div className="setting-row" onClick={() => setLangOpen(true)}>
          <div className="s-icon" style={{ background: 'var(--c-accent-l)' }}>🌐</div>
          <div className="s-body">
            <div className="s-name">{t('profile.language')}</div>
            <div className="s-val">{currentLang?.nativeName}</div>
          </div>
          <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
        </div>
        <div className="setting-row" onClick={handleGoogleRowClick}>
          <div className="s-icon" style={{ background: 'var(--c-red-l)' }}>📅</div>
          <div className="s-body">
            <div className="s-name">{t('profile.googleCalendar')}</div>
            <div className="s-val">
              {googleConnecting
                ? t('profile.googleConnecting')
                : googleAccessToken
                  ? t('profile.googleConnected')
                  : t('profile.googleNotConnected')}
            </div>
          </div>
          <div className={`toggle-track ${googleAccessToken ? 'on' : 'off'}`}>
            <div className="toggle-knob" />
          </div>
        </div>
        <div className="setting-row" onClick={() => navigate('s-onboarding')}>
          <div className="s-icon" style={{ background: 'var(--c-bg)' }}>👤</div>
          <div className="s-body">
            <div className="s-name">{t('profile.editProfile')}</div>
            <div className="s-val">{t('profile.editProfileSub')}</div>
          </div>
          <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
        </div>

        <div className="logout-btn" onClick={() => navigate('s-onboarding')}>{t('profile.logout')}</div>
        <div style={{ height: '20px' }} />
      </div>
      <BottomNav active="s-profile" />

      {/* ── 언어 선택 시트 ── */}
      {langOpen && (
        <div className="source-modal-overlay" onClick={() => setLangOpen(false)}>
          <div className="channel-modal-sheet" onClick={e => e.stopPropagation()}>
            <div className="source-modal-handle" />
            <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--c-t1)', textAlign: 'center', padding: '4px 0 12px' }}>
              {t('profile.languageSheetTitle')}
            </div>
            {languages.map(l => (
              <button
                key={l.code}
                className={`channel-modal-btn ${l.code === locale ? 'primary' : 'secondary'}`}
                onClick={() => chooseLanguage(l.code)}
              >
                {l.nativeName}{l.code === locale ? ' ✓' : ''}
              </button>
            ))}
            <button className="channel-modal-btn secondary" onClick={() => setLangOpen(false)}>
              {t('common.cancel')}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
