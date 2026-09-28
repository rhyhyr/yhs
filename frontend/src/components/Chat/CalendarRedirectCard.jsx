/**
 * 캘린더 연동 완료 후 "캘린더로 바로 이동하시겠어요?" 카드
 */
import { useI18n } from '../../i18n';

export default function CalendarRedirectCard({ onConfirm, onDismiss }) {
  const { t } = useI18n();
  return (
    <div className="cl-confirm cl-redirect-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">🎉</span>
        <span className="cl-redirect-label">{t('calendarLink.doneLabel')}</span>
      </div>
      <div className="cl-confirm-body">
        {t('calendarLink.goBody')}
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>{t('common.yes')}</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>{t('common.no')}</button>
      </div>
    </div>
  );
}
