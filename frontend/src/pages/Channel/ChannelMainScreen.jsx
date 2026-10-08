import { useApp } from '../../hooks/useApp';
import { BackIcon, SearchIcon } from '../../components/Common/icons';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';

const TAG_FILTERS = ['all', 'extend', 'd2', 'docs', 'immigration'];

const CARDS = [
  { key: 'q1', tags: ['d2', 'extend', 'docs'], time: { key: 'daysAgo', n: 3 } },
  { key: 'q2', tags: ['extend', 'period'],     time: { key: 'weeksAgo', n: 1 } },
  { key: 'q3', tags: ['immigration'],          time: { key: 'weeksAgo', n: 2 } },
];

export default function ChannelMainScreen() {
  const { navigate, back, showToast, channelFilter, setChannelFilter } = useApp();
  const { t, localizeChannel } = useI18n();
  const filterLabel = f => (f === 'all' ? t('search.filter.all') : t(`tags.${f}`));
  return (
    <>
      <div className="slim-header">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
        <div className="slim-ch-name">{localizeChannel(getChannel('visa')).name}</div>
        <div className="slim-rag">{t('common.ragActive')}</div>
      </div>
      <div className="ch-tabs">
        <div className="ch-tab" onClick={() => navigate('s-visa')}>{t('channel.chatTab')}</div>
        <div className="ch-tab active">{t('channel.knowledgeTab')}</div>
      </div>
      <div className="search-bar">
        <SearchIcon />
        <span>{t('channel.searchInChannel')}</span>
      </div>
      <div className="filter-row">
        {TAG_FILTERS.map(f => (
          <button key={f} className={`filter-chip${channelFilter === f ? ' active' : ''}`} onClick={() => { setChannelFilter(f); showToast(t('toast.filterApplied', { name: filterLabel(f) })); }}>{filterLabel(f)}</button>
        ))}
      </div>
      <div className="scroll-area" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px 0 12px' }}>
        {CARDS.map(({ key, tags, time }) => (
          <div key={key} className="k-card" onClick={() => navigate('s-knowledge')}>
            <div className="k-card-body">
              <span className="ghost-badge" style={{ marginBottom: '4px', display: 'inline-block' }}>{t('common.example')}</span>
              <div className="k-q">{t(`kb.${key}.q`)}</div>
              <div className="k-preview">{t(`kb.${key}.preview`)}</div>
            </div>
            <div className="k-card-foot">
              <div style={{ display: 'flex', gap: '5px' }}>
                {tags.map(tag => (
                  <span key={tag} className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>{t(`tags.${tag}`)}</span>
                ))}
              </div>
              <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>{t(`time.${time.key}`, { n: time.n })}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
