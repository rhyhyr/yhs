import { useApp } from '../../hooks/useApp';

const NAV_ITEMS = [
  { id: 's-home', icon: '⊞', label: '홈' },
  { id: 's-main', icon: '💬', label: '채팅' },
  { id: 's-calendar', icon: '📅', label: '캘린더' },
  { id: 's-search', icon: '🗂️', label: '기록' },
  { id: 's-profile', icon: '👤', label: '내정보' },
];

export default function BottomNav({ active }) {
  const { navigate } = useApp();
  return (
    <div className="bottom-nav">
      {NAV_ITEMS.map(item => (
        <div
          key={item.id}
          className={`bnav-item${active === item.id ? ' active' : ''}`}
          onClick={() => navigate(item.id)}
        >
          <div className="bnav-icon">{item.icon}</div>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
