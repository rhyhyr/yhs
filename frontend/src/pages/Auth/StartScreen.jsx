import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { APP_NAME } from '../../api/config';
import { BackIcon } from '../../components/Common/icons';

/**
 * 시작 화면 (언어 선택 다음) — 계정 없이 바로 사용
 * 회원가입·로그인은 아직 없음. 프로필 등은 이 기기(localStorage)에만 저장된다.
 * - 프로필을 아직 입력하지 않았으면 → 기본 정보 입력(onboarding)
 * - 이미 있으면 → 홈
 */
export default function StartScreen() {
  const { back, resetTo, showToast, userProfile } = useApp();
  const { t, locale, languages } = useI18n();
  const langName = languages.find(l => l.code === locale)?.nativeName;

  function handleStart() {
    // 정보 입력을 이미 했거나 건너뛴 적이 있으면(onboardedAt) 바로 홈으로.
    // (onboardedAt 도입 전에 저장된 프로필은 학교가 있으면 입력한 것으로 본다)
    if (userProfile?.onboardedAt || userProfile?.school) {
      showToast(userProfile.name
        ? t('auth.welcomeBack', { name: userProfile.name })
        : t('auth.welcomeBackNoName'));
      resetTo('s-home');
    } else {
      resetTo('s-onboarding');
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-top">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <button className="auth-lang-pill" onClick={back}>🌐 {langName}</button>
      </div>

      <div className="auth-hero">
        <img className="auth-logo" src="/icons/icon-192.png" alt="" />
        <div className="auth-app">{APP_NAME}</div>
      </div>

      <div className="auth-title">{t('auth.startTitle')}</div>
      <div className="auth-sub" style={{ whiteSpace: 'pre-line' }}>{t('auth.startSub')}</div>

      <div className="auth-points">
        <div>🛂 {t('auth.point1')}</div>
        <div>📎 {t('auth.point2')}</div>
        <div>🌐 {t('auth.point3')}</div>
      </div>

      <div style={{ flex: 1 }} />
      <button className="cta-primary auth-cta" onClick={handleStart}>
        {t('auth.start')}
      </button>
    </div>
  );
}
