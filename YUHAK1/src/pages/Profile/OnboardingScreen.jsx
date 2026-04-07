import { useApp } from '../../hooks/useApp';

export default function OnboardingScreen() {
  const { navigate, showToast, visaChip, setVisaChip, langs, setLangs } = useApp();
  return (
    <div style={{ flex: 1, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
      <div className="ob-hero">
        <span className="ob-mark">🎓</span>
        <div className="ob-h">YHS</div>
        <div className="ob-p">한국 유학 생활, 더 쉽게<br />비자·학교·생활 모두 안내해드려요</div>
      </div>
      <button className="social-btn" onClick={() => showToast('Google 로그인 화면으로 이동합니다')}>
        <span style={{ fontSize: '18px' }}>🌐</span> Google로 시작하기
      </button>
      <div style={{ padding: '0 16px 12px', textAlign: 'center', fontSize: '12px', color: 'var(--c-t3)' }}>카카오 로그인은 추후 지원 예정입니다</div>
      <div style={{ height: '1px', background: 'var(--c-border)', margin: '0 0 16px' }} />
      <div className="ob-steps">
        <div className="ob-step-dot done" />
        <div className="ob-step-dot active" />
        <div className="ob-step-dot" />
      </div>
      <div className="form-sec">기본 정보 입력</div>
      <div className="form-note">국적·학교·비자 유형만 입력하면 바로 시작할 수 있어요</div>
      <div className="form-group" style={{ marginTop: '8px' }}>
        <div className="f-label">국적</div>
        <div className="f-input filled">🇨🇳 중국 <span style={{ color: 'var(--c-t3)' }}>▾</span></div>
      </div>
      <div className="form-group">
        <div className="f-label">학교</div>
        <div className="f-input filled">부산대학교</div>
      </div>
      <div className="form-group">
        <div className="f-label">비자 유형</div>
        <div className="chip-row">
          {['D-2 학생', 'D-4 어학연수', 'F-2 거주', '기타'].map(v => (
            <button key={v} className={`sel-chip${visaChip === v ? ' on' : ''}`} onClick={() => setVisaChip(v)}>{v}</button>
          ))}
        </div>
      </div>
      <div className="ob-note">📅 비자 만료일은 비자 채널에서 대화할 때 입력할 수 있어요</div>
      <div className="form-sec">사용 언어</div>
      <div className="lang-grid">
        {[['ko','🇰🇷','한국어','Korean'],['zh','🇨🇳','중국어','Chinese'],['en','🇺🇸','영어','English'],['vi','🇻🇳','베트남어','Vietnamese']].map(([key, flag, name, sub]) => (
          <div key={key} className={`lang-card${langs[key] ? ' on' : ''}`} onClick={() => setLangs(l => ({ ...l, [key]: !l[key] }))}>
            <div className="lang-flag">{flag}</div>
            <div className="lang-name">{name}</div>
            <div className="lang-sub">{sub}</div>
          </div>
        ))}
      </div>
      <button className="cta-primary" onClick={() => navigate('s-bridge')}>시작하기 →</button>
      <div className="footnote">국적·학교·비자 유형만으로 맞춤 채널이 자동 생성됩니다</div>
    </div>
  );
}
