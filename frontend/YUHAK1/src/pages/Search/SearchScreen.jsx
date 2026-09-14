import { useApp } from '../../hooks/useApp';
import { SearchIcon } from '../../components/Common/icons';
import BottomNav from '../../components/Common/BottomNav';

export default function SearchScreen() {
  const { navigate, showToast, activeFilter, setActiveFilter, activeFilter2, setActiveFilter2 } = useApp();
  return (
    <>
      {/* ── 헤더 ── */}
      <div className="topbar">
        <div style={{ flex: 1 }}>
          <div className="tb-title">답변 기록</div>
          <div className="tb-sub">AI가 답변한 기록을 검색해요</div>
        </div>
      </div>

      {/* ── 역할 안내 배너 ── */}
      <div style={{
        margin: '0 14px 6px',
        padding: '9px 13px',
        background: 'var(--c-accent-l)',
        border: '1px solid var(--c-accent-m)',
        borderRadius: '11px',
        fontSize: '12px',
        color: 'var(--c-accent)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '8px',
      }}>
        <span>💡 새 질문은 <strong>채팅 탭</strong>에서 할 수 있어요</span>
        <span
          style={{ fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
          onClick={() => navigate('s-main')}
        >
          채팅으로 →
        </span>
      </div>

      {/* ── 검색창 ── */}
      <div className="search-bar">
        <SearchIcon />
        <span style={{ color: 'var(--c-t3)' }}>저장된 답변 검색...</span>
      </div>

      {/* ── 채널 필터 ── */}
      <div className="filter-row">
        {['전체', '🛂 비자', '🏫 학교', '💼 취업', '🏠 주거'].map(f => (
          <button
            key={f}
            className={`filter-chip${activeFilter === f ? ' active' : ''}`}
            onClick={() => { setActiveFilter(f); showToast(f + ' 필터가 적용됐습니다'); }}
          >{f}</button>
        ))}
      </div>

      {/* ── 태그 필터 ── */}
      <div className="filter-row" style={{ paddingTop: 0 }}>
        {['#연장', '#D-2', '#서류', '#출입국'].map(f => (
          <button
            key={f}
            className={`filter-chip${activeFilter2 === f ? ' active' : ''}`}
            style={{ fontSize: '11px' }}
            onClick={() => { setActiveFilter2(f); showToast(f + ' 필터가 적용됐습니다'); }}
          >{f}</button>
        ))}
      </div>

      {/* ── 결과 수 ── */}
      <div style={{ padding: '4px 14px 8px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>
        저장된 답변 2건
      </div>

      {/* ── 결과 목록 ── */}
      <div className="scroll-area" style={{ paddingBottom: '12px' }}>

        <div className="result-card" onClick={() => navigate('s-knowledge')}>
          <div className="result-inner">
            <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="result-body">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--c-purple)', fontWeight: 600 }}>비자 &amp; 체류</span>
                <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '6px', background: 'var(--c-green-l)', color: 'var(--c-green)', fontWeight: 600 }}>AI 답변</span>
              </div>
              <div className="result-q">
                <span style={{ fontSize: '10px', color: 'var(--c-t3)', marginRight: '4px', fontWeight: 600 }}>Q.</span>
                비자 연장하려면 뭐가 필요해요?
              </div>
              <div className="result-p">D-2 비자 연장 서류입니다. ① 여권 원본 ② 외국인등록증...</div>
              <div className="result-foot">
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="r-time">3일 전</span>
                  <span style={{ fontSize: '12px', color: 'var(--c-accent)', fontWeight: 500 }}>답변 보기 ›</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="result-card" onClick={() => navigate('s-knowledge')}>
          <div className="result-inner">
            <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="result-body">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--c-purple)', fontWeight: 600 }}>비자 &amp; 체류</span>
                <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '6px', background: 'var(--c-green-l)', color: 'var(--c-green)', fontWeight: 600 }}>AI 답변</span>
              </div>
              <div className="result-q">
                <span style={{ fontSize: '10px', color: 'var(--c-t3)', marginRight: '4px', fontWeight: 600 }}>Q.</span>
                비자 연장 신청 기간이 언제예요?
              </div>
              <div className="result-p">만료일 4개월 전부터 신청 가능합니다. 늦어도 1개월 전에...</div>
              <div className="result-foot">
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="r-time">1주 전</span>
                  <span style={{ fontSize: '12px', color: 'var(--c-accent)', fontWeight: 500 }}>답변 보기 ›</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <BottomNav active="s-search" />
    </>
  );
}
