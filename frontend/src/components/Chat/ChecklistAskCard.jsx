import { getMockChecklist } from '../../data/mockChecklistData';

/**
 * 1단계: "체크리스트를 만들까요?" 확인 카드
 */
export default function ChecklistAskCard({ checklistId, onConfirm, onDismiss }) {
  const checklist = getMockChecklist(checklistId);
  if (!checklist) return null;

  return (
    <div className="cl-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">📋</span>
        <span className="cl-confirm-chip"
          style={{ color: checklist.color, background: `${checklist.color}18` }}>
          {checklist.title}
        </span>
      </div>
      <div className="cl-confirm-body">
        이 내용으로 체크리스트를 만들까요?
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>만들기</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>아니요</button>
      </div>
    </div>
  );
}
