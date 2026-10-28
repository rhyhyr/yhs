import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { VISA_OPTIONS } from '../../data/visaTypes';
import { APP_NAME } from '../../api/config';

const GRADE_OPTIONS = ['1', '2', '3', '4', '5', '6'];

const INPUT_STYLE = {
  border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px',
  width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)',
};

/**
 * 맞춤 답변용 기본 정보 입력 (계정 없이 사용 — 이 기기에만 저장)
 *
 * 필수: 비자 유형(기본 D-2), 학교(기본 동아대학교) / 선택: 학년, 국적, 부를 이름
 * 여기서 받은 비자 유형·학교·학년·국적은 채팅 질문에 함께 보내져 맞춤 답변에 쓰인다 (api/chat.js).
 * 사용 언어는 첫 화면(언어 선택)에서 고른 앱 언어로 자동 저장 — 여기서 다시 묻지 않음.
 * "나중에 입력할게요"로 건너뛸 수 있고, 내 정보 › 프로필 수정에서 언제든 다시 입력 가능.
 */
export default function OnboardingScreen() {
  const { navigate, back, showToast, userProfile, saveUserProfile } = useApp();
  const { t, locale } = useI18n();
  const alreadyOnboarded = !!userProfile?.onboardedAt;

  const [form, setForm] = useState({
    visaType: userProfile?.visaType || VISA_OPTIONS[0].value,
    school: userProfile?.school || t('onboarding.schoolDefault'),
    grade: userProfile?.grade ?? '',
    nationality: userProfile?.nationality ?? '',
    name: userProfile?.name ?? '',
  });

  function setField(key, val) {
    setForm(f => ({ ...f, [key]: val }));
  }

  const canSubmit = form.school.trim() && form.visaType;

  function handleStart() {
    if (!canSubmit) {
      showToast(t('onboarding.required'));
      return;
    }
    saveUserProfile({
      ...userProfile,
      ...form,
      name: form.name.trim(),
      school: form.school.trim(),
      nationality: form.nationality.trim(),
      languages: [locale],
      onboardedAt: userProfile?.onboardedAt ?? Date.now(),
    });
    navigate('s-bridge');
  }

  // 건너뛰기 — 처음이면 "봤음"만 기록하고 다음으로, 프로필 수정 중이면 그냥 뒤로
  function handleSkip() {
    if (alreadyOnboarded) { back(); return; }
    saveUserProfile({ ...userProfile, languages: [locale], onboardedAt: Date.now() });
    navigate('s-bridge');
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
      <div className="ob-hero">
        <span className="ob-mark">🎓</span>
        <div className="ob-h">{APP_NAME}</div>
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

      <div className="form-group">
        <div className="f-label">{t('onboarding.school')} <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <input
          className="f-input"
          style={INPUT_STYLE}
          placeholder={t('onboarding.schoolPh')}
          value={form.school}
          onChange={e => setField('school', e.target.value)}
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
        <div className="f-label">{t('onboarding.nationality')}</div>
        <input
          className="f-input"
          style={INPUT_STYLE}
          placeholder={t('onboarding.nationalityPh')}
          value={form.nationality}
          onChange={e => setField('nationality', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">{t('onboarding.name')}</div>
        <input
          className="f-input"
          style={INPUT_STYLE}
          placeholder={t('onboarding.namePh')}
          value={form.name}
          onChange={e => setField('name', e.target.value)}
        />
      </div>

      <div className="ob-note">{t('onboarding.visaNote')}</div>

      <button
        className="cta-primary"
        onClick={handleStart}
        style={{ opacity: canSubmit ? 1 : 0.5 }}
      >
        {t('onboarding.start')}
      </button>
      <button className="ob-skip" onClick={handleSkip}>{t('onboarding.skip')}</button>
      <div className="footnote">{t('onboarding.footnote')}</div>
    </div>
  );
}
