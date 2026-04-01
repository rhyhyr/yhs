import { useApp } from '../hooks/useApp';
import { BackIcon } from '../components/icons';

export default function StepGuideScreen() {
  const { back, showToast, steps, toggleStep, checkedCount, total, pct, grp1Checked, grp2Checked } = useApp();
  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          비자 채널
        </div>
      </div>
      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>D-2 비자 연장 절차</div>
        <div className="tb-sub">출입국관리사무소 방문 기준</div>
      </div>
      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" id="prog-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="prog-label">
          <span id="prog-txt">{checkedCount} / {total} 단계 완료</span>
          <span id="prog-pct" style={{ color: 'var(--c-green)' }}>{pct}%</span>
        </div>
      </div>
      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        <div className="step-card">
          <div className="step-card-hdr">
            <span>📁 서류 준비</span>
            <span id="grp1-prog" style={{ fontSize: '11px', fontWeight: 400 }}>{grp1Checked}/4 완료</span>
          </div>
          {steps.slice(0, 4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleStep(step.id)}>
              <div className={`step-cb${step.checked ? ' checked' : step.current ? ' current' : ''}`}>
                {step.checked ? '✓' : ''}
              </div>
              <div className="step-label">
                <div className={`step-text${step.checked ? ' done' : ''}`} style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}>
                  {step.text}
                </div>
                {step.sub && (
                  <div className={`step-sub${step.checked ? ' done' : ''}`} style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}>
                    {step.sub}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="step-card">
          <div className="step-card-hdr">
            <span>📋 신청</span>
            <span style={{ fontSize: '11px', fontWeight: 400 }}>{grp2Checked}/2 완료</span>
          </div>
          {steps.slice(4).map(step => (
            <div key={step.id} className="step-row" onClick={() => toggleStep(step.id)}>
              <div className={`step-cb${step.checked ? ' checked' : ''}`}>
                {step.checked ? '✓' : ''}
              </div>
              <div className="step-label">
                <div className={`step-text${step.checked ? ' done' : ''}`} style={{ color: step.checked ? undefined : 'var(--c-t3)' }}>
                  {step.text}
                </div>
                {step.sub && (
                  <div className={`step-sub${step.checked ? ' done' : ''}`} style={{ color: step.checked ? undefined : 'var(--c-t3)' }}>
                    {step.sub}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="save-note">✅ 체크 상태는 자동 저장됩니다. 앱을 닫아도 유지돼요.</div>
        <div style={{ margin: '4px 14px' }}>
          <button className="qa-btn" style={{ width: '100%', textAlign: 'left', borderRadius: '11px', padding: '12px 14px' }} onClick={() => showToast('주의사항을 불러옵니다')}>⚠️ 주의사항 더 보기</button>
        </div>
      </div>
    </>
  );
}
