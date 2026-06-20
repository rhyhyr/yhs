import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';

export default function SchoolChecklistScreen() {
  const {
    back, showToast,
    schoolSteps, toggleSchoolStep,
    schoolCheckedCount, schoolTotal, schoolPct,
    schoolGrp1Checked, schoolGrp2Checked,
  } = useApp();

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          학교생활 채널
        </div>
      </div>

      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>수강신청 & 등록 준비</div>
        <div className="tb-sub">학교 포털 기준 · 학기 시작 전 확인</div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" style={{ width: `${schoolPct}%` }} />
        </div>
        <div className="prog-label">
          <span>{schoolCheckedCount} / {schoolTotal} 단계 완료</span>
          <span style={{ color: 'var(--c-green)' }}>{schoolPct}%</span>
        </div>
      </div>

      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {/* 등록 준비 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>📅 등록 준비</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{schoolGrp1Checked}/4 완료</span>
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
            <span>📋 수강신청</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{schoolGrp2Checked}/3 완료</span>
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

        <div className="save-note">✅ 체크 상태는 자동 저장됩니다. 앱을 닫아도 유지돼요.</div>

        <div style={{ margin: '4px 14px' }}>
          <button
            className="qa-btn"
            style={{ width: '100%', textAlign: 'left', borderRadius: '11px', padding: '12px 14px' }}
            onClick={() => showToast('학교 포털로 이동합니다')}
          >
            🏫 학교 포털 바로가기
          </button>
        </div>
      </div>
    </>
  );
}
