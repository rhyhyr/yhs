import { useApp } from '../hooks/useApp';
import { BackIcon, SearchIcon } from '../components/icons';

export default function ChannelMainScreen() {
  const { navigate, back, showToast, channelFilter, setChannelFilter } = useApp();
  return (
    <>
      <div className="slim-header">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
        <div className="slim-ch-name">비자 &amp; 체류</div>
        <div className="slim-rag">RAG 활성</div>
      </div>
      <div className="ch-tabs">
        <div className="ch-tab" onClick={() => navigate('s-visa')}>💬 채팅</div>
        <div className="ch-tab active">📚 지식 카드</div>
      </div>
      <div className="search-bar">
        <SearchIcon />
        <span>채널 내 대화 검색...</span>
      </div>
      <div className="filter-row">
        {['전체','#연장','#D-2','#서류','#출입국'].map(f => (
          <button key={f} className={`filter-chip${channelFilter === f ? ' active' : ''}`} onClick={() => { setChannelFilter(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
        ))}
      </div>
      <div className="scroll-area" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px 0 12px' }}>
        <div className="k-card" onClick={() => navigate('s-knowledge')}>
          <div className="k-card-body">
            <div className="k-q">비자 연장하려면 뭐가 필요해요?</div>
            <div className="k-preview">D-2 비자 연장 서류입니다. ① 여권 원본 ② 외국인등록증 ③ 재학증명서 (영문)...</div>
          </div>
          <div className="k-card-foot">
            <div style={{ display: 'flex', gap: '5px' }}>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#서류</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>3일 전</span>
          </div>
        </div>
        <div className="k-card" onClick={() => navigate('s-knowledge')}>
          <div className="k-card-body">
            <div className="k-q">비자 연장 신청 기간이 언제예요?</div>
            <div className="k-preview">만료일 4개월 전부터 신청 가능합니다. 늦어도 만료 1개월 전에는...</div>
          </div>
          <div className="k-card-foot">
            <div style={{ display: 'flex', gap: '5px' }}>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#기간</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>1주 전</span>
          </div>
        </div>
        <div className="k-card" onClick={() => navigate('s-knowledge')}>
          <div className="k-card-body">
            <div className="k-q">Hi Korea에서 온라인 신청이 가능한가요?</div>
            <div className="k-preview">네, Hi Korea(www.hikorea.go.kr)에서 온라인으로 비자 연장 신청이 가능합니다...</div>
          </div>
          <div className="k-card-foot">
            <div style={{ display: 'flex', gap: '5px' }}>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#출입국</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>2주 전</span>
          </div>
        </div>
      </div>
    </>
  );
}
