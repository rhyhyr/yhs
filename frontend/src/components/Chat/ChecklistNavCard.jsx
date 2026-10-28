import { useI18n } from '../../i18n';

/**
 * 채팅 영역에 붙는 체크리스트 이동 카드. 탭하면 onClick 으로 체크리스트 화면을 연다.
 * (선택형 안내 트리의 마지막 단계에서 쓴다 — data/guideFlows.js)
 */
export default function ChecklistNavCard({ title, count, onClick, color = '#2155CD' }) {
  const { t } = useI18n();
  return (
    <div
      className="cl-nav-card"
      style={{ borderColor: color, background: `${color}0D` }}
      onClick={onClick}
    >
      <div className="cl-nav-icon">📋</div>
      <div className="cl-nav-body">
        <div className="cl-nav-title" style={{ color }}>{t('checklist.navTitle')}</div>
        <div className="cl-nav-sub">{t('checklist.navSub', { title, n: count })}</div>
      </div>
      <div className="cl-nav-arrow" style={{ color }}>›</div>
    </div>
  );
}
