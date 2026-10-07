/**
 * 3단계: "캘린더에 연동하시겠습니까?" 확인 카드
 */
import { useI18n } from '../../i18n';

export default function CalendarLinkCard({ onConfirm, onDismiss }) {
  const { t } = useI18n();
  return (
    <div className="cl-confirm cl-cal-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">📅</span>
        <span className="cl-cal-label">{t('calendarLink.label')}</span>
      </div>
      <div className="cl-confirm-body">
        {t('calendarLink.body')}
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>{t('common.yes')}</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>{t('common.no')}</button>
      </div>
    </div>
  );
}
