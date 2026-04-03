import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';
import SourceModal from '../../components/Chat/SourceModal';

const SOURCES = [
  { label: '법무부 출입국관리법 시행규칙 (2024)', detail: '제76조 – 체류자격 변경·연장 절차 및 제출서류' },
  { label: 'Hi Korea 외국인 안내', detail: 'www.hikorea.go.kr · 비자 연장 온라인 신청 가이드' },
];

export default function KnowledgeScreen() {
  const { navigate, back, showToast } = useApp();
  const [sourceOpen, setSourceOpen] = useState(false);
  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '7px', background: 'var(--c-purple-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px' }}>🛂</div>
          <span style={{ fontSize: '13px', color: 'var(--c-t2)' }}>비자 &amp; 체류 채널</span>
        </div>
      </div>
      <div className="scroll-area">
        <div className="kd-q-box">
          <div className="kd-q-label">Q. 원본 질문</div>
          <div className="kd-q-text">비자 연장하려면 뭐가 필요해요?</div>
        </div>
        <div style={{ padding: '8px 14px 6px', display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
          <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
          <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#서류</span>
          <span style={{ fontSize: '11px', color: 'var(--c-t3)', display: 'flex', alignItems: 'center', marginLeft: '4px' }}>3일 전</span>
        </div>
        <div className="kd-block-text">D-2 비자 연장에 필요한 서류입니다. 출입국관리사무소 방문 신청 또는 Hi Korea 온라인 신청 모두 가능합니다.</div>
        <div className="kd-list-block">
          <div className="kd-list-title">📋 필요 서류</div>
          {[
            '여권 원본 + 사본 1부 (유효기간 6개월 이상)',
            '외국인등록증 원본',
            '재학증명서 (영문)',
            '수수료 60,000원',
          ].map((item, i) => (
            <div key={i} className="kd-list-item">
              <div className="kd-num">{i + 1}</div>{item}
            </div>
          ))}
        </div>
        <div className="kd-source" onClick={() => setSourceOpen(true)}>
          📎 출처: 법무부 출입국관리법 시행규칙 (2024) · Hi Korea 외국인 안내
        </div>
        <div className="kd-section-lbl">⚡ Action Guide</div>
        <div className="cta-card" onClick={() => navigate('s-step')} style={{ margin: '0 14px 14px' }}>
          <div className="cta-icon">📋</div>
          <div className="cta-body">
            <div className="cta-title">비자 연장 절차 보기</div>
            <div className="cta-sub">6단계 체크리스트 · 진행 현황 추적</div>
          </div>
          <div className="cta-arrow">›</div>
        </div>
        <div className="kd-section-lbl">🔗 관련 질문</div>
        <div className="related-q" onClick={() => showToast('관련 질문을 불러옵니다')}>
          비자 연장 신청 기간이 언제예요?
          <span style={{ color: 'var(--c-t3)', fontSize: '18px' }}>›</span>
        </div>
        <div className="related-q" onClick={() => showToast('관련 질문을 불러옵니다')}>
          Hi Korea 온라인 신청이 가능한가요?
          <span style={{ color: 'var(--c-t3)', fontSize: '18px' }}>›</span>
        </div>
        <div style={{ height: '16px' }} />
      </div>

      <SourceModal
        isOpen={sourceOpen}
        onClose={() => setSourceOpen(false)}
        sources={SOURCES}
      />
    </>
  );
}
