import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';
import { useI18n } from '../../i18n';

export default function SchoolChecklistScreen() {
  const {
    back, showToast,
    schoolSteps: rawSchoolSteps, toggleSchoolStep,
    schoolCheckedCount, schoolTotal, schoolPct,
    schoolGrp1Checked, schoolGrp2Checked,
  } = useApp();
  const { t, localizeSteps } = useI18n();
  const schoolSteps = localizeSteps(rawSchoolSteps, 'school-registration');

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          {t('guide.schoolChannel')}
        </div>
      </div>

      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>{t('guide.schoolTitle')}</div>
        <div className="tb-sub">{t('guide.schoolBasis')}</div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" style={{ width: `${schoolPct}%` }} />
        </div>
        <div className="prog-label">
          <span>{t('guide.progress', { done: schoolCheckedCount, total: schoolTotal })}</span>
          <span style={{ color: 'var(--c-green)' }}>{schoolPct}%</span>
        </div>
      </div>

      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {/* 등록 준비 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>{t('guide.regPrep')}</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{t('guide.groupProgress', { done: schoolGrp1Checked, total: 4 })}</span>
          </div>
          {schoolSteps.slice(0, 4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleSchoolStep(step.id)}>
              <div className={`step-cb${step.checked ? ' checked' : step.current ? ' current' : ''}`}>
                {step.checked ? '✓' : ''}
              </div>
              <div className="step-label">
                <div
                  className={`step-text${step.checked ? ' done' : ''}`}
                  style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}
                >
                  {step.text}
                </div>
                {step.sub && (
                  <div
                    className={`step-sub${step.checked ? ' done' : ''}`}
                    style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}
                  >
                    {step.sub}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 수강신청 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>{t('guide.courseReg')}</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{t('guide.groupProgress', { done: schoolGrp2Checked, total: schoolSteps.length - 4 })}</span>
          </div>
          {schoolSteps.slice(4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleSchoolStep(step.id)}>
              <div className={`step-cb${step.checked ? ' checked' : ''}`}>
                {step.checked ? '✓' : ''}
              </div>
              <div className="step-label">
                <div
                  className={`step-text${step.checked ? ' done' : ''}`}
                  style={{ color: step.checked ? undefined : 'var(--c-t3)' }}
                >
                  {step.text}
                </div>
                {step.sub && (
                  <div
                    className={`step-sub${step.checked ? ' done' : ''}`}
                    style={{ color: step.checked ? undefined : 'var(--c-t3)' }}
                  >
                    {step.sub}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="save-note">{t('guide.autoSave')}</div>

        <div style={{ margin: '4px 14px' }}>
          <button
            className="qa-btn"
            style={{ width: '100%', textAlign: 'left', borderRadius: '11px', padding: '12px 14px' }}
            onClick={() => showToast(t('guide.portalToast'))}
          >
            {t('guide.portalLink')}
          </button>
        </div>
      </div>
    </>
  );
}
