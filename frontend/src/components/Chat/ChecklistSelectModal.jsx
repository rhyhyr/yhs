import { useState } from 'react';
import { getMockChecklist } from '../../data/mockChecklistData';
import { downloadIcsFile } from '../../utils/googleCalendar';
import { useI18n } from '../../i18n';

/**
 * 캘린더 연동할 항목을 선택하는 바텀 시트 모달
 *
 * props:
 *   checklistId — 표시할 체크리스트 ID
 *   onConfirm   — (selectedItemIds: number[], dateOverrides: Record<number,string>) => void
 *   onClose     — 모달 닫기
 */
export default function ChecklistSelectModal({ checklistId, onConfirm, onClose }) {
  const { t, fmt, localizeChecklist } = useI18n();
  const checklist = localizeChecklist(getMockChecklist(checklistId));
  const [selected, setSelected] = useState(
    () => new Set(checklist?.items.map(i => i.id) ?? [])
  );

  // 항목별로 사용자가 직접 바꾼 날짜 — 키: item.id, 값: 'YYYY-MM-DD'.
  // 여기 없는 항목은 체크리스트 원래 날짜를 그대로 씀.
  const [dateOverrides, setDateOverrides] = useState({});
  // 지금 날짜 입력 중인 항목 id (한 번에 하나만 편집)
  const [editingId, setEditingId] = useState(null);

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

  function changeDate(id, value) {
    if (!value) return;
    setDateOverrides(prev => ({ ...prev, [id]: value }));
  }

  const formatDueDate = (dateStr) => {
    const [, m, d] = dateStr.split('-').map(Number);
    return fmt(new Date(2000, m - 1, d), { month: 'long', day: 'numeric' });
  };

  const allSelected = selected.size === checklist.items.length;
  const count = selected.size;

  // 선택한 항목을 통째로 .ics 파일로 내려받기 — 구글 캘린더 "가져오기"로 한 번에 등록 가능
  // (다른 캘린더 앱도 다 호환되는 표준 파일이라 구글에만 묶이지 않음)
  function handleExportIcs() {
    const events = checklist.items
      .filter(item => selected.has(item.id))
      .map(item => ({
        uid: `${checklist.id}-${item.id}`,
        title: item.text,
        description: item.sub || '',
        dateStr: dateOverrides[item.id] ?? item.dueDate,
      }));
    downloadIcsFile(checklist.title, events);
  }

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
            const checked  = selected.has(item.id);
            const dueDate  = dateOverrides[item.id] ?? item.dueDate;
            const editing  = editingId === item.id;
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

                {editing ? (
                  <input
                    type="date"
                    className="cl-sheet-date-input"
                    value={dueDate}
                    autoFocus
                    onClick={e => e.stopPropagation()}
                    onChange={e => changeDate(item.id, e.target.value)}
                    onBlur={() => setEditingId(null)}
                  />
                ) : (
                  <div
                    className="cl-sheet-item-date"
                    style={{ color: checklist.color, background: `${checklist.color}14` }}
                    onClick={e => { e.stopPropagation(); setEditingId(item.id); }}
                  >
                    {formatDueDate(dueDate)} ✏️
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 구글 캘린더(등) 가져오기용 .ics 내보내기 */}
        <div style={{ padding: '0 16px 4px' }}>
          <button
            className="qa-btn"
            style={{ width: '100%', textAlign: 'center', borderRadius: '11px', padding: '10px 14px' }}
            disabled={count === 0}
            onClick={handleExportIcs}
          >
            {t('checklist.exportIcs', { n: count })}
          </button>
        </div>

        {/* 하단 버튼 */}
        <div className="cl-sheet-footer">
          <button className="cl-sheet-cancel" onClick={onClose}>{t('common.cancel')}</button>
          <button
            className="cl-sheet-confirm"
            disabled={count === 0}
            onClick={() => onConfirm(Array.from(selected), dateOverrides)}
          >
            {count > 0 ? t('checklist.linkN', { n: count }) : t('checklist.selectPrompt')}
          </button>
        </div>
      </div>
    </div>
  );
}
