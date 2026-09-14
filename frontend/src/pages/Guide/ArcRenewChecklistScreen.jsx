import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';

export default function ArcRenewChecklistScreen() {
  const {
    back, showToast,
    arcSteps, toggleArcStep,
    arcCheckedCount, arcTotal, arcPct,
    arcGrp1Checked, arcGrp2Checked,
  } = useApp();

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          비자 채널
        </div>
      </div>

      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>외국인등록증 재발급 절차</div>
        <div className="tb-sub">출입국관리사무소 방문 기준</div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" style={{ width: `${arcPct}%` }} />
        </div>
        <div className="prog-label">
          <span>{arcCheckedCount} / {arcTotal} 단계 완료</span>
          <span style={{ color: 'var(--c-green)' }}>{arcPct}%</span>
        </div>
      </div>

      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {/* 서류 준비 */}
        <div className="step-card">
          <div className="step-card-hdr">
            <span>📁 서류 준비</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{arcGrp1Checked}/4 완료</span>
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
            <span>📋 신청</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{arcGrp2Checked}/3 완료</span>
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

        <div className="save-note">✅ 체크 상태는 자동 저장됩니다. 앱을 닫아도 유지돼요.</div>

        <div style={{ margin: '4px 14px' }}>
          <button
            className="qa-btn"
            style={{ width: '100%', textAlign: 'left', borderRadius: '11px', padding: '12px 14px' }}
            onClick={() => showToast('Hi Korea 안내 페이지로 이동합니다')}
          >
            🌐 Hi Korea 온라인 신청 바로가기
          </button>
        </div>
      </div>
    </>
  );
}
