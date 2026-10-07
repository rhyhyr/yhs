import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';

const NAV_ITEMS = [
  { id: 's-home', icon: '⊞', label: 'nav.home' },
  { id: 's-main', icon: '💬', label: 'nav.chat' },
  { id: 's-calendar', icon: '📅', label: 'nav.calendar' },
  { id: 's-search', icon: '🗂️', label: 'nav.history' },
  { id: 's-profile', icon: '👤', label: 'nav.profile' },
];

export default function BottomNav({ active }) {
  const { navigate } = useApp();
  const { t } = useI18n();
  return (
    <div className="bottom-nav">
      {NAV_ITEMS.map(item => (
        <div
          key={item.id}
          className={`bnav-item${active === item.id ? ' active' : ''}`}
          onClick={() => navigate(item.id)}
        >
          <div className="bnav-icon">{item.icon}</div>
          <span>{t(item.label)}</span>
        </div>
      ))}
    </div>
  );
}
