import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';
import { useI18n } from '../../i18n';

export default function ArcRenewChecklistScreen() {
  const {
    back, showToast,
    arcSteps: rawArcSteps, toggleArcStep,
    arcCheckedCount, arcTotal, arcPct,
    arcGrp1Checked, arcGrp2Checked,
  } = useApp();
  const { t, localizeSteps } = useI18n();
  const arcSteps = localizeSteps(rawArcSteps, 'arc-renew');

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          {t('visa.backToChannel')}
        </div>
      </div>

      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>{t('guide.arcTitle')}</div>
        <div className="tb-sub">{t('guide.officeBasis')}</div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" style={{ width: `${arcPct}%` }} />
        </div>
        <div className="prog-label">
          <span>{t('guide.progress', { done: arcCheckedCount, total: arcTotal })}</span>
          <span style={{ color: 'var(--c-green)' }}>{arcPct}%</span>
        </div>
      </div>

      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {/* 서류 준비 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>{t('guide.docsPrep')}</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{t('guide.groupProgress', { done: arcGrp1Checked, total: 4 })}</span>
          </div>
          {arcSteps.slice(0, 4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleArcStep(step.id)}>
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

        {/* 신청 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>{t('guide.apply')}</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{t('guide.groupProgress', { done: arcGrp2Checked, total: arcSteps.length - 4 })}</span>
          </div>
          {arcSteps.slice(4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleArcStep(step.id)}>
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
            onClick={() => showToast(t('guide.hikoreaToast'))}
          >
            {t('guide.hikoreaLink')}
          </button>
        </div>
      </div>
    </>
  );
}
