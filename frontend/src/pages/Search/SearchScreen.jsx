import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';
import { SearchIcon } from '../../components/Common/icons';
import BottomNav from '../../components/Common/BottomNav';

const CHANNEL_FILTERS = ['all', 'visa', 'school', 'job', 'house'];
const TAG_FILTERS = ['extend', 'd2', 'docs', 'immigration'];

// 채팅으로 실제 대화한 기록이 없을 때를 대비한 고정 예시 2건 (항상 "예시" 배지와 함께 표시)
const EXAMPLE_RESULTS = [
  { key: 'q1', channelId: 'visa', tags: ['d2', 'extend'], time: { key: 'daysAgo', n: 3 } },
  { key: 'q2', channelId: 'visa', tags: ['extend'],       time: { key: 'weeksAgo', n: 1 } },
];

// 채널 ID → 그 채널의 채팅 화면 (HomeScreen/ChatScreen과 같은 매핑)
const CHANNEL_SCREEN = {
  visa: 's-visa', school: 's-school', job: 's-job', house: 's-house', insurance: 's-insurance',
};

export default function SearchScreen() {
  const {
    navigate, showToast,
    activeFilter, setActiveFilter, activeFilter2, setActiveFilter2,
    answerHistory,
  } = useApp();
  const { t, localizeChannel } = useI18n();

  // 실제 대화 기록 — 채널 필터만 적용 (태그는 실제 답변에 아직 안 달려 있어서 예시 카드에만 의미 있음)
  const realResults = activeFilter === 'all'
    ? answerHistory
    : answerHistory.filter(e => e.channelId === activeFilter);

  // 예시 카드도 같은 채널 필터를 받는다 (전부 비자 채널 내용이라 다른 채널 필터를 고르면 안 보임)
  const exampleResults = EXAMPLE_RESULTS.filter(
    r => activeFilter === 'all' || r.channelId === activeFilter
  );

  function goToSource(entry) {
    const screen = CHANNEL_SCREEN[entry.channelId];
    if (!screen) return;
    navigate(screen, { highlightMessageId: entry.messageId });
  }

  function renderMeta(channelId) {
    const ch = localizeChannel(getChannel(channelId));
    return ch ?? { icon: '💬', iconBg: 'var(--c-accent-l)', name: channelId };
  }

  return (
    <>
      {/* ── 헤더 ── */}
      <div className="topbar">
        <div style={{ flex: 1 }}>
          <div className="tb-title">{t('search.title')}</div>
          <div className="tb-sub">{t('search.subtitle')}</div>
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
        <span>{t('search.bannerPre')} <strong>{t('search.bannerBold')}</strong>{t('search.bannerPost')}</span>
        <span
          style={{ fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
          onClick={() => navigate('s-main')}
        >
          {t('search.toChat')}
        </span>
      </div>

      {/* ── 검색창 ── */}
      <div className="search-bar">
        <SearchIcon />
        <span style={{ color: 'var(--c-t3)' }}>{t('search.placeholder')}</span>
      </div>

      {/* ── 채널 필터 ── */}
      <div className="filter-row">
        {CHANNEL_FILTERS.map(f => (
          <button
            key={f}
            className={`filter-chip${activeFilter === f ? ' active' : ''}`}
            onClick={() => { setActiveFilter(f); showToast(t('toast.filterApplied', { name: t(`search.filter.${f}`) })); }}
          >{t(`search.filter.${f}`)}</button>
        ))}
      </div>

      {/* ── 태그 필터 ── */}
      <div className="filter-row" style={{ paddingTop: 0 }}>
        {TAG_FILTERS.map(f => (
          <button
            key={f}
            className={`filter-chip${activeFilter2 === f ? ' active' : ''}`}
            style={{ fontSize: '11px' }}
            onClick={() => { setActiveFilter2(f); showToast(t('toast.filterApplied', { name: t(`tags.${f}`) })); }}
          >{t(`tags.${f}`)}</button>
        ))}
      </div>

      {/* ── 결과 수 ── */}
      <div style={{ padding: '4px 14px 8px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>
        {t('search.resultCount', { n: realResults.length + exampleResults.length })}
      </div>

      {/* ── 결과 목록 ── */}
      <div className="scroll-area" style={{ paddingBottom: '12px' }}>

        {/* 실제 대화에서 나온 답변 */}
        {realResults.map(entry => {
          const meta = renderMeta(entry.channelId);
          return (
            <div key={entry.messageId} className="result-card" onClick={() => goToSource(entry)}>
              <div className="result-inner">
                <div className="result-ch-icon" style={{ background: meta.iconBg }}>{meta.icon}</div>
                <div className="result-body">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--c-purple)', fontWeight: 600 }}>{meta.name}</span>
                    <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '6px', background: 'var(--c-green-l)', color: 'var(--c-green)', fontWeight: 600 }}>{t('search.aiAnswer')}</span>
                  </div>
                  <div className="result-q">
                    <span style={{ fontSize: '10px', color: 'var(--c-t3)', marginRight: '4px', fontWeight: 600 }}>Q.</span>
                    {entry.question}
                  </div>
                  <div className="result-p">{entry.answer}</div>
                  <div className="result-foot">
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="r-time">{t('time.justNow')}</span>
                      <span style={{ fontSize: '12px', color: 'var(--c-accent)', fontWeight: 500 }}>{t('search.viewAnswer')}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* 예시 — 실제 기록 유무와 상관없이 항상 "예시" 배지와 함께 맨 아래 고정 표시 */}
        {exampleResults.length > 0 && (
          <div className="sec-lbl" style={{ marginTop: realResults.length > 0 ? '4px' : 0, color: 'var(--c-t3)' }}>
            {t('home.belowAreExamples')}
          </div>
        )}
        {exampleResults.map(({ key, channelId, tags, time }) => {
          const meta = renderMeta(channelId);
          return (
            <div key={key} className="result-card" onClick={() => navigate('s-knowledge')}>
              <div className="result-inner">
                <div className="result-ch-icon" style={{ background: meta.iconBg }}>{meta.icon}</div>
                <div className="result-body">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--c-purple)', fontWeight: 600 }}>{meta.name}</span>
                    <span className="ghost-badge">{t('common.example')}</span>
                  </div>
                  <div className="result-q">
                    <span style={{ fontSize: '10px', color: 'var(--c-t3)', marginRight: '4px', fontWeight: 600 }}>Q.</span>
                    {t(`kb.${key}.q`)}
                  </div>
                  <div className="result-p">{t(`kb.${key}.preview`)}</div>
                  <div className="result-foot">
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {tags.map(tag => (
                        <span key={tag} className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>{t(`tags.${tag}`)}</span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="r-time">{t(`time.${time.key}`, { n: time.n })}</span>
                      <span style={{ fontSize: '12px', color: 'var(--c-accent)', fontWeight: 500 }}>{t('search.viewAnswer')}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {realResults.length === 0 && exampleResults.length === 0 && (
          <div style={{ padding: '32px 14px', textAlign: 'center', color: 'var(--c-t3)', fontSize: '13px' }}>
            {t('search.empty')}
          </div>
        )}
      </div>

      <BottomNav active="s-search" />
    </>
  );
}
