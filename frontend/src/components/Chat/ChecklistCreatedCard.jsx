import { getMockChecklist } from '../../data/mockChecklistData';
import { useI18n } from '../../i18n';

function fmtDate(dateStr) {
  const [, m, d] = dateStr.split('-').map(Number);
  return `${m}/${d}`;
}

/**
 * 2단계: 생성된 체크리스트를 채팅 영역에 인라인으로 표시
 */
export default function ChecklistCreatedCard({ checklistId }) {
  const { t, localizeChecklist } = useI18n();
  const checklist = localizeChecklist(getMockChecklist(checklistId));
  if (!checklist) return null;

  return (
    <div className="cl-created-card">
      <div className="cl-created-header">
        <span className="cl-created-icon">✅</span>
        <span className="cl-created-title">{t('checklist.createdTitle', { title: checklist.title })}</span>
      </div>
      <div className="cl-created-list">
        {checklist.items.map(item => (
          <div key={item.id} className="cl-created-item">
            <span className="cl-created-cb" />
            <span className="cl-created-text">{item.text}</span>
            <span className="cl-created-date"
              style={{ color: checklist.color, background: `${checklist.color}14` }}>
              {fmtDate(item.dueDate)}
            </span>
          </div>
        ))}
      </div>
      <div className="cl-created-footer">{t('checklist.total', { n: checklist.items.length })}</div>
    </div>
  );
}
