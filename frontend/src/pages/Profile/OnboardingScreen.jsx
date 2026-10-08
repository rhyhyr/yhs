import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { VISA_OPTIONS } from '../../data/visaTypes';

// [코드, 국기, 그 언어로 쓴 이름] — 화면에 보이는 이름은 i18n languageNames.{코드}
const LANG_OPTIONS = [
  ['ko', '🇰🇷', '한국어'],
  ['zh', '🇨🇳', '中文'],
  ['en', '🇺🇸', 'English'],
  ['vi', '🇻🇳', 'Tiếng Việt'],
];
const GRADE_OPTIONS = ['1', '2', '3', '4', '5', '6'];

function langsArrayToMap(arr) {
  return { ko: arr.includes('ko'), zh: arr.includes('zh'), en: arr.includes('en'), vi: arr.includes('vi') };
}

export default function OnboardingScreen() {
  const { navigate, showToast, userProfile, saveUserProfile } = useApp();
  const { t } = useI18n();

  const [form, setForm] = useState({
    name: userProfile?.name ?? '',
    nationality: userProfile?.nationality ?? '',
    school: userProfile?.school ?? '',
    department: userProfile?.department ?? '',
    grade: userProfile?.grade ?? '',
    visaType: userProfile?.visaType || VISA_OPTIONS[0].value,
    languages: userProfile?.languages?.length ? userProfile.languages : ['ko', 'zh'],
  });

  const langsMap = langsArrayToMap(form.languages);

  function setField(key, val) {
    setForm(f => ({ ...f, [key]: val }));
  }

  function toggleLang(key) {
    setForm(f => {
      const has = f.languages.includes(key);
      return {
        ...f,
        languages: has ? f.languages.filter(l => l !== key) : [...f.languages, key],
      };
    });
  }

  const canSubmit = form.name.trim() && form.school.trim() && form.visaType;

  function handleStart() {
    if (!canSubmit) {
      showToast(t('onboarding.required'));
      return;
    }
    saveUserProfile({ ...form, name: form.name.trim(), school: form.school.trim() });
    navigate('s-bridge');
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
      <div className="ob-hero">
        <span className="ob-mark">🎓</span>
        <div className="ob-h">YuGuide AI</div>
        <div className="ob-p" style={{ whiteSpace: 'pre-line' }}>{t('onboarding.tagline')}</div>
      </div>

      <div style={{ height: '1px', background: 'var(--c-border)', margin: '0 0 16px' }} />

      <div className="ob-steps">
        <div className="ob-step-dot done" />
        <div className="ob-step-dot active" />
        <div className="ob-step-dot" />
      </div>

      <div className="form-sec">{t('onboarding.basicInfo')}</div>
      <div className="form-note">{t('onboarding.basicNote')}</div>

      <div className="form-group" style={{ marginTop: '8px' }}>
        <div className="f-label">{t('onboarding.name')} <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder={t('onboarding.namePh')}
          value={form.name}
          onChange={e => setField('name', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.nationality')}</div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder={t('onboarding.nationalityPh')}
          value={form.nationality}
          onChange={e => setField('nationality', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.school')} <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder={t('onboarding.schoolPh')}
          value={form.school}
          onChange={e => setField('school', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.department')}</div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder={t('onboarding.departmentPh')}
          value={form.department}
          onChange={e => setField('department', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.grade')}</div>
        <div className="chip-row">
          {GRADE_OPTIONS.map(g => (
            <button
              key={g}
              className={`sel-chip${form.grade === g ? ' on' : ''}`}
              onClick={() => setField('grade', form.grade === g ? '' : g)}
            >
              {t('common.gradeN', { n: g })}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.visaType')} <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <div className="chip-row">
          {VISA_OPTIONS.map(v => (
            <button
              key={v.value}
              className={`sel-chip${form.visaType === v.value ? ' on' : ''}`}
              onClick={() => setField('visaType', v.value)}
            >
              {t(`visaTypes.${v.key}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="ob-note">{t('onboarding.visaNote')}</div>

      <div className="form-sec">{t('onboarding.languages')}</div>
      <div className="lang-grid">
        {LANG_OPTIONS.map(([key, flag, native]) => (
          <div
            key={key}
            className={`lang-card${langsMap[key] ? ' on' : ''}`}
            onClick={() => toggleLang(key)}
          >
            <div className="lang-flag">{flag}</div>
            <div className="lang-name">{t(`languageNames.${key}`)}</div>
            {native !== t(`languageNames.${key}`) && <div className="lang-sub">{native}</div>}
          </div>
        ))}
      </div>

      <button
        className="cta-primary"
        onClick={handleStart}
        style={{ opacity: canSubmit ? 1 : 0.5 }}
      >
        {t('onboarding.start')}
      </button>
      <div className="footnote">{t('onboarding.footnote')}</div>
    </div>
  );
}
