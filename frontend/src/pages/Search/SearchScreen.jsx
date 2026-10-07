import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';
import { SearchIcon } from '../../components/Common/icons';
import BottomNav from '../../components/Common/BottomNav';

const CHANNEL_FILTERS = ['all', 'visa', 'school', 'job', 'house'];
const TAG_FILTERS = ['extend', 'd2', 'docs', 'immigration'];

const RESULTS = [
  { key: 'q1', tags: ['d2', 'extend'], time: { key: 'daysAgo', n: 3 } },
  { key: 'q2', tags: ['extend'],       time: { key: 'weeksAgo', n: 1 } },
];

export default function SearchScreen() {
  const { navigate, showToast, activeFilter, setActiveFilter, activeFilter2, setActiveFilter2 } = useApp();
  const { t, localizeChannel } = useI18n();
  const visaName = localizeChannel(getChannel('visa')).name;
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
        {t('search.resultCount', { n: RESULTS.length })}
      </div>

      {/* ── 결과 목록 ── */}
      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {RESULTS.map(({ key, tags, time }) => (
          <div key={key} className="result-card" onClick={() => navigate('s-knowledge')}>
            <div className="result-inner">
              <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
              <div className="result-body">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--c-purple)', fontWeight: 600 }}>{visaName}</span>
                  <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '6px', background: 'var(--c-green-l)', color: 'var(--c-green)', fontWeight: 600 }}>{t('search.aiAnswer')}</span>
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
        ))}
      </div>

      <BottomNav active="s-search" />
    </>
  );
}
