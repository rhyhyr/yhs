/**
 * 3단계: "캘린더에 연동하시겠습니까?" 확인 카드
 */
export default function CalendarLinkCard({ onConfirm, onDismiss }) {
  return (
    <div className="cl-confirm cl-cal-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">📅</span>
        <span className="cl-cal-label">캘린더 연동</span>
      </div>
      <div className="cl-confirm-body">
        이 일정을 캘린더에 연동하시겠습니까?
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>네</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>아니요</button>
      </div>
    </div>
  );
}
