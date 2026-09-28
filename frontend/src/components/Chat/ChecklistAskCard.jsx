import { getMockChecklist } from '../../data/mockChecklistData';
import { useI18n } from '../../i18n';

/**
 * 1단계: "체크리스트를 만들까요?" 확인 카드
 */
export default function ChecklistAskCard({ checklistId, onConfirm, onDismiss }) {
  const { t, localizeChecklist } = useI18n();
  const checklist = localizeChecklist(getMockChecklist(checklistId));
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
        {t('checklist.askBody')}
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>{t('checklist.make')}</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>{t('common.no')}</button>
      </div>
    </div>
  );
}
