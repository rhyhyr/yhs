import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { APP_NAME } from '../../api/config';

// 언어 코드 → 배지 글자. 목록 자체는 i18n 에 등록된 언어(LOCALES)를 그대로 쓴다.
// (국기 이모지는 Windows 브라우저에서 'KR' 같은 글자로 깨져 보여서 글자 배지를 씀)
const BADGES = { ko: '한', zh: '中', en: 'En', vi: 'Vi' };

/**
 * 앱 첫 화면 — 언어 선택
 * 고르는 즉시 앱 전체 언어가 바뀌므로, 이 화면의 문구도 바로 그 언어로 바뀐다.
 * 답변 언어(profile.languages)도 함께 바꿔서, 백엔드가 이 언어로 답하게 한다.
 */
export default function LanguageScreen() {
  const { navigate, updateUserProfile } = useApp();
  const { t, locale, setLocale, languages } = useI18n();

  return (
    <div className="auth-wrap">
      <div className="auth-hero">
        <img className="auth-logo" src="/icons/icon-192.png" alt="" />
        <div className="auth-app">{APP_NAME}</div>
      </div>

      <div className="auth-title">{t('auth.langTitle')}</div>
      <div className="auth-sub">{t('auth.langSub')}</div>

      <div className="auth-lang-list">
        {languages.map(({ code, nativeName }) => (
          <button
            key={code}
            className={`auth-lang${locale === code ? ' on' : ''}`}
            onClick={() => { setLocale(code); updateUserProfile({ languages: [code] }); }}
          >
            <span className="auth-lang-badge">{BADGES[code] ?? code}</span>
            <span className="auth-lang-name">{nativeName}</span>
            <span className="auth-lang-check">{locale === code ? '✓' : ''}</span>
          </button>
        ))}
      </div>

      <div style={{ flex: 1 }} />
      <button className="cta-primary auth-cta" onClick={() => navigate('s-start')}>
        {t('auth.continue')}
      </button>
    </div>
  );
}
