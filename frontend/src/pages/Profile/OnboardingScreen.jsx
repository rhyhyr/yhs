import { useState } from 'react';
import { useApp } from '../../hooks/useApp';

const VISA_OPTIONS = ['D-2 학생', 'D-4 어학연수', 'F-2 거주', '기타'];
const LANG_OPTIONS = [
  ['ko', '🇰🇷', '한국어', 'Korean'],
  ['zh', '🇨🇳', '중국어', 'Chinese'],
  ['en', '🇺🇸', '영어', 'English'],
  ['vi', '🇻🇳', '베트남어', 'Vietnamese'],
];
const GRADE_OPTIONS = ['1', '2', '3', '4', '5', '6'];

function langsArrayToMap(arr) {
  return { ko: arr.includes('ko'), zh: arr.includes('zh'), en: arr.includes('en'), vi: arr.includes('vi') };
}

export default function OnboardingScreen() {
  const { navigate, showToast, userProfile, saveUserProfile } = useApp();

  const [form, setForm] = useState({
    name: userProfile?.name ?? '',
    nationality: userProfile?.nationality ?? '',
    school: userProfile?.school ?? '',
    department: userProfile?.department ?? '',
    grade: userProfile?.grade ?? '',
    visaType: userProfile?.visaType || 'D-2 학생',
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
      showToast('이름, 학교, 비자 유형을 입력해주세요');
      return;
    }
    saveUserProfile({ ...form, name: form.name.trim(), school: form.school.trim() });
    navigate('s-bridge');
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
      <div className="ob-hero">
        <span className="ob-mark">🎓</span>
        <div className="ob-h">UniGuide AI</div>
        <div className="ob-p">한국 유학 생활, 더 쉽게<br />비자·학교·생활 모두 안내해드려요</div>
      </div>

      <div style={{ height: '1px', background: 'var(--c-border)', margin: '0 0 16px' }} />

      <div className="ob-steps">
        <div className="ob-step-dot done" />
        <div className="ob-step-dot active" />
        <div className="ob-step-dot" />
      </div>

      <div className="form-sec">기본 정보 입력</div>
      <div className="form-note">국적·학교·비자 유형만 입력하면 바로 시작할 수 있어요</div>

      <div className="form-group" style={{ marginTop: '8px' }}>
        <div className="f-label">이름 <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder="이름을 입력하세요"
          value={form.name}
          onChange={e => setField('name', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">국적</div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder="예: 중국, 베트남, 미국"
          value={form.nationality}
          onChange={e => setField('nationality', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">학교 <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder="예: 부산대학교"
          value={form.school}
          onChange={e => setField('school', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">학과</div>
        <input
          className="f-input"
          style={{ border: '1px solid var(--c-border)', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', width: '100%', boxSizing: 'border-box', background: 'var(--c-bg)' }}
          placeholder="예: 컴퓨터공학과"
          value={form.department}
          onChange={e => setField('department', e.target.value)}
        />
      </div>

      <div className="form-group">
        <div className="f-label">학년</div>
        <div className="chip-row">
          {GRADE_OPTIONS.map(g => (
            <button
              key={g}
              className={`sel-chip${form.grade === g ? ' on' : ''}`}
              onClick={() => setField('grade', form.grade === g ? '' : g)}
            >
              {g}학년
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <div className="f-label">비자 유형 <span style={{ color: 'var(--c-red)' }}>*</span></div>
        <div className="chip-row">
          {VISA_OPTIONS.map(v => (
            <button
              key={v}
              className={`sel-chip${form.visaType === v ? ' on' : ''}`}
              onClick={() => setField('visaType', v)}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      <div className="ob-note">📅 비자 만료일은 비자 채널에서 대화할 때 입력할 수 있어요</div>

      <div className="form-sec">사용 언어</div>
      <div className="lang-grid">
        {LANG_OPTIONS.map(([key, flag, name, sub]) => (
          <div
            key={key}
            className={`lang-card${langsMap[key] ? ' on' : ''}`}
            onClick={() => toggleLang(key)}
          >
            <div className="lang-flag">{flag}</div>
            <div className="lang-name">{name}</div>
            <div className="lang-sub">{sub}</div>
          </div>
        ))}
      </div>

      <button
        className="cta-primary"
        onClick={handleStart}
        style={{ opacity: canSubmit ? 1 : 0.5 }}
      >
        시작하기 →
      </button>
      <div className="footnote">국적·학교·비자 유형만으로 맞춤 채널이 자동 생성됩니다</div>
    </div>
  );
}
