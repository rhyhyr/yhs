import { getMockChecklist } from '../../data/mockChecklistData';

function fmtDate(dateStr) {
  const [, m, d] = dateStr.split('-').map(Number);
  return `${m}/${d}`;
}

/**
 * 2단계: 생성된 체크리스트를 채팅 영역에 인라인으로 표시
 */
export default function ChecklistCreatedCard({ checklistId }) {
  const checklist = getMockChecklist(checklistId);
  if (!checklist) return null;

  return (
    <div className="cl-created-card">
      <div className="cl-created-header">
        <span className="cl-created-icon">✅</span>
        <span className="cl-created-title">{checklist.title} 체크리스트</span>
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
      <div className="cl-created-footer">총 {checklist.items.length}개 항목</div>
    </div>
  );
}
