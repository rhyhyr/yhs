import { getMockChecklist } from '../../data/mockChecklistData';
import { useI18n } from '../../i18n';

/**
 * AI 응답 이후 채팅 영역 하단에 표시되는 캘린더 연동 확인 카드
 *
 * props:
 *   checklistId — 연동할 체크리스트 ID
 *   onConfirm   — "네" 클릭 시 콜백
 *   onDismiss   — "아니요" 클릭 시 콜백
 */
export default function ChecklistGeneratedConfirm({ checklistId, onConfirm, onDismiss }) {
  const { t, localizeChecklist } = useI18n();
  const checklist = localizeChecklist(getMockChecklist(checklistId));
  if (!checklist) return null;

  return (
    <div className="cl-confirm">
      <div className="cl-confirm-top">
        <span className="cl-confirm-icon">📋</span>
        <span className="cl-confirm-chip" style={{ color: checklist.color, background: `${checklist.color}18` }}>
          {checklist.title}
        </span>
      </div>
      <div className="cl-confirm-body" style={{ whiteSpace: 'pre-line' }}>
        {t('checklist.generatedBody')}
      </div>
      <div className="cl-confirm-actions">
        <button className="cl-confirm-yes" onClick={onConfirm}>{t('common.yes')}</button>
        <button className="cl-confirm-no"  onClick={onDismiss}>{t('common.no')}</button>
      </div>
    </div>
  );
}
