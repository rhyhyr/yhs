import { getMockChecklist } from '../../data/mockChecklistData';

/**
 * AI 응답 이후 채팅 영역 하단에 표시되는 캘린더 연동 확인 카드
 *
 * props:
 *   checklistId — 연동할 체크리스트 ID
 *   onConfirm   — "네" 클릭 시 콜백
 *   onDismiss   — "아니요" 클릭 시 콜백
 */
export default function ChecklistGeneratedConfirm({ checklistId, onConfirm, onDismiss }) {
  const checklist = getMockChecklist(checklistId);
  if (!checklist) return null;

  return (
    <div className="cl-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">📋</span>
        <span className="cl-confirm-chip" style={{ color: checklist.color, background: `${checklist.color}18` }}>
          {checklist.title}
        </span>
      </div>
      <div className="cl-confirm-body">
        체크리스트가 생성되었습니다.<br />
        이 내용을 캘린더에 연동하시겠습니까?
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>네</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>아니요</button>
      </div>
    </div>
  );
}
