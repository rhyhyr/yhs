import { useState } from 'react';
import { getMockChecklist } from '../../data/mockChecklistData';
import { useI18n } from '../../i18n';

/**
 * 캘린더 연동할 항목을 선택하는 바텀 시트 모달
 *
 * props:
 *   checklistId — 표시할 체크리스트 ID
 *   onConfirm   — (selectedItemIds: number[]) => void
 *   onClose     — 모달 닫기
 */
export default function ChecklistSelectModal({ checklistId, onConfirm, onClose }) {
  const { t, fmt, localizeChecklist } = useI18n();
  const checklist = localizeChecklist(getMockChecklist(checklistId));
  const [selected, setSelected] = useState(
    () => new Set(checklist?.items.map(i => i.id) ?? [])
  );

  if (!checklist) return null;

  function toggle(id) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected(prev =>
      prev.size === checklist.items.length
        ? new Set()
        : new Set(checklist.items.map(i => i.id))
    );
  }

  const formatDueDate = (dateStr) => {
    const [, m, d] = dateStr.split('-').map(Number);
    return fmt(new Date(2000, m - 1, d), { month: 'long', day: 'numeric' });
  };

  const allSelected = selected.size === checklist.items.length;
  const count = selected.size;

  return (
    <div className="source-modal-overlay" onClick={onClose}>
      <div className="cl-sheet" onClick={e => e.stopPropagation()}>
        <div className="source-modal-handle" />

        {/* 헤더 */}
        <div className="cl-sheet-header">
          <div>
            <div className="cl-sheet-title">{t('checklist.createdTitle', { title: checklist.title })}</div>
            <div className="cl-sheet-subtitle">{t('checklist.selectSubtitle')}</div>
          </div>
          <button className="cl-sheet-all-btn" onClick={toggleAll}>
            {allSelected ? t('checklist.deselectAll') : t('checklist.selectAll')}
          </button>
        </div>

        {/* 항목 목록 */}
        <div className="cl-sheet-list">
          {checklist.items.map(item => {
            const checked = selected.has(item.id);
            return (
              <div
                key={item.id}
                className={`cl-sheet-item${checked ? ' checked' : ''}`}
                onClick={() => toggle(item.id)}
              >
                <div className={`cl-sheet-cb${checked ? ' checked' : ''}`}>
                  {checked && '✓'}
                </div>
                <div className="cl-sheet-item-content">
                  <div className="cl-sheet-item-title">{item.text}</div>
                  {item.sub && <div className="cl-sheet-item-sub">{item.sub}</div>}
                </div>
                <div
                  className="cl-sheet-item-date"
                  style={{ color: checklist.color, background: `${checklist.color}14` }}
                >
                  {formatDueDate(item.dueDate)}
                </div>
              </div>
            );
          })}
        </div>

        {/* 하단 버튼 */}
        <div className="cl-sheet-footer">
          <button className="cl-sheet-cancel" onClick={onClose}>{t('common.cancel')}</button>
          <button
            className="cl-sheet-confirm"
            disabled={count === 0}
            onClick={() => onConfirm(Array.from(selected))}
          >
            {count > 0 ? t('checklist.linkN', { n: count }) : t('checklist.selectPrompt')}
          </button>
        </div>
      </div>
    </div>
  );
}
