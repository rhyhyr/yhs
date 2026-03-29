import { useApp } from '../hooks/useApp';
import { SearchIcon } from '../components/icons';
import BottomNav from '../components/BottomNav';

export default function SearchScreen() {
  const { navigate, showToast, activeFilter, setActiveFilter, activeFilter2, setActiveFilter2 } = useApp();
  return (
    <>
      <div className="topbar">
        <div className="tb-title" style={{ flex: 1 }}>검색</div>
        <div className="tb-sub" style={{ fontSize: '11px', color: 'var(--c-t3)' }}>과거 대화 전체 탐색</div>
      </div>
      <div className="search-bar" style={{ marginTop: '6px' }}>
        <SearchIcon />
        <span>비자 연장</span>
      </div>
      <div className="filter-row">
        {['전체','🛂 비자','🏫 학교','💼 취업','🏠 주거'].map(f => (
          <button key={f} className={`filter-chip${activeFilter === f ? ' active' : ''}`} onClick={() => { setActiveFilter(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
        ))}
      </div>
      <div className="filter-row" style={{ paddingTop: 0 }}>
        {['#연장','#D-2','#서류','#출입국'].map(f => (
          <button key={f} className={`filter-chip${activeFilter2 === f ? ' active' : ''}`} style={{ fontSize: '11px' }} onClick={() => { setActiveFilter2(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
        ))}
      </div>
      <div style={{ padding: '4px 14px 8px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>검색 결과 2건</div>
      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        <div className="result-card" onClick={() => navigate('s-knowledge')}>
          <div className="result-inner">
            <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="result-body">
              <div className="result-q">비자 연장하려면 뭐가 필요해요?</div>
              <div className="result-p">D-2 비자 연장 서류입니다. ① 여권 원본 ② 외국인등록증...</div>
              <div className="result-foot">
                <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
                <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                <span className="r-time">3일 전</span>
              </div>
            </div>
          </div>
        </div>
        <div className="result-card" onClick={() => navigate('s-knowledge')}>
          <div className="result-inner">
            <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="result-body">
              <div className="result-q">비자 연장 신청 기간이 언제예요?</div>
              <div className="result-p">만료일 4개월 전부터 신청 가능합니다. 늦어도 1개월 전에...</div>
              <div className="result-foot">
                <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                <span className="r-time">1주 전</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <BottomNav active="s-search" />
    </>
  );
}
