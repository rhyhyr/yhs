/**
 * 캘린더 연동 완료 후 "캘린더로 바로 이동하시겠어요?" 카드
 */
export default function CalendarRedirectCard({ onConfirm, onDismiss }) {
  return (
    <div className="cl-confirm cl-redirect-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">🎉</span>
        <span className="cl-redirect-label">연동 완료</span>
      </div>
      <div className="cl-confirm-body">
        캘린더로 바로 이동하시겠어요?
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>네</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>아니요</button>
      </div>
    </div>
  );
}
