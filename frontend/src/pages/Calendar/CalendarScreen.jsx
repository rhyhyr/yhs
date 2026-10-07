import { useState, useEffect, useMemo } from 'react';
import { useApp } from '../../hooks/useApp';
import { getCalendarEvents, mergeEvents } from '../../api/calendar';
import { formatDateKey } from '../../api/mockData';
import BottomNav from '../../components/Common/BottomNav';
import { useI18n } from '../../i18n';

// 체크리스트→캘린더 연동을 지원하는 채널 → 그 채널의 채팅 화면 id
// (지금은 비자/학교 채널만 체크리스트 흐름이 있음)
const CHECKLIST_CHANNEL_SCREEN = { visa: 's-visa', school: 's-school' };

export default function CalendarScreen() {
  const { navigate, showToast, chatCalendarItems, navParams } = useApp();
  const { t, fmt } = useI18n();
  const [calDate, setCalDate]             = useState(new Date());
  const [selectedDateKey, setSelectedDateKey] = useState(null);
  const [apiEvents, setApiEvents]         = useState({});

  // 채팅 캘린더 연동 시 해당 날짜로 자동 이동
  useEffect(() => {
    const target = navParams?.targetDate;
    if (!target) return;
    const [y, m] = target.split('-').map(Number);
    setCalDate(new Date(y, m - 1, 1));
    setSelectedDateKey(target);
  }, [navParams?.targetDate]); // eslint-disable-line react-hooks/exhaustive-deps

  const year  = calDate.getFullYear();
  const month = calDate.getMonth();
  const today = new Date();

  useEffect(() => {
    getCalendarEvents(year, month).then(setApiEvents).catch(() => setApiEvents({}));
    setSelectedDateKey(null);
  }, [year, month]);

  // 최종 이벤트 맵: API 이벤트 + 채팅으로 추가된 항목만
  const events = useMemo(
    () => mergeEvents(apiEvents, chatCalendarItems),
    [apiEvents, chatCalendarItems]
  );

  function changeMonth(diff) {
    setCalDate(prev => {
      const d = new Date(prev);
      d.setMonth(d.getMonth() + diff);
      return d;
    });
  }

  function goToday() {
    const t = new Date();
    setCalDate(new Date(t.getFullYear(), t.getMonth(), 1));
    setSelectedDateKey(formatDateKey(t.getFullYear(), t.getMonth(), t.getDate()));
  }

  const resolvedSelected = selectedDateKey || (() => {
    const isCurrentMonth =
      today.getFullYear() === year && today.getMonth() === month;
    if (isCurrentMonth) return formatDateKey(year, month, today.getDate());
    const firstEvent = Object.keys(events).sort().find(k => {
      const [y, m] = k.split('-').map(Number);
      return y === year && m === month + 1;
    });
    return firstEvent || formatDateKey(year, month, 1);
  })();

  const selectedEvents = events[resolvedSelected] || [];
  const [selY, selM, selD] = resolvedSelected.split('-').map(Number);
  const selDate = new Date(selY, selM - 1, selD);
  // 2023-01-01 은 일요일 — 요일 머리글을 현재 언어로 만들기 위한 기준일
  const weekLabels = Array.from({ length: 7 }, (_, i) =>
    fmt(new Date(2023, 0, 1 + i), { weekday: 'short' }));

  const firstWeekday  = new Date(year, month, 1).getDay();
  const daysInMonth   = new Date(year, month + 1, 0).getDate();
  const prevMonthDays = new Date(year, month, 0).getDate();
  const totalCurrent  = firstWeekday + daysInMonth;
  const nextPadding   = totalCurrent % 7 === 0 ? 0 : 7 - (totalCurrent % 7);

  const cells = [
    ...Array.from({ length: firstWeekday }, (_, i) => ({
      day: prevMonthDays - firstWeekday + i + 1, kind: 'other',
    })),
    ...Array.from({ length: daysInMonth }, (_, i) => {
      const day = i + 1;
      const key = formatDateKey(year, month, day);
      const isToday =
        today.getFullYear() === year &&
        today.getMonth()    === month &&
        today.getDate()     === day;
      return { day, key, kind: 'current', isToday, isSelected: key === resolvedSelected, events: events[key] || [] };
    }),
    ...Array.from({ length: nextPadding }, (_, i) => ({ day: i + 1, kind: 'other' })),
  ];

  return (
    <>
      <div className="topbar">
        <div className="tb-title" style={{ flex: 1 }}>{t('calendar.title')}</div>
        <div className="cal-nav-group">
          <button className="cal-today-btn" onClick={goToday}>{t('calendar.today')}</button>
          <button className="cal-nav-btn" onClick={() => changeMonth(-1)}>‹</button>
          <button className="cal-nav-btn" onClick={() => changeMonth(1)}>›</button>
        </div>
      </div>

      <div className="scroll-area">
        <div className="cal-month-label">{fmt(new Date(year, month, 1), { year: 'numeric', month: 'long' })}</div>

        <div className="cal-weekdays">
          {weekLabels.map((d, i) => (
            <div key={i} className={`cal-weekday${i === 0 ? ' sun' : i === 6 ? ' sat' : ''}`}>{d}</div>
          ))}
        </div>

        <div className="cal-grid">
          {cells.map((cell, i) => {
            if (cell.kind === 'other') {
              return (
                <div key={`o-${i}`} className="cal-cell other-month">
                  <span className="cal-date">{cell.day}</span>
                </div>
              );
            }
            let cls = 'cal-cell';
            if (cell.isToday)    cls += ' today';
            if (cell.isSelected) cls += ' selected';
            return (
              <div key={cell.key} className={cls} onClick={() => setSelectedDateKey(cell.key)}>
                <span className="cal-date">{cell.day}</span>
                {cell.events.length > 0 && (
                  <div className="cal-dots">
                    {cell.events.slice(0, 3).map((evt, j) => (
                      <div key={j} className="cal-dot"
                        style={{ background: evt.isCompleted ? 'var(--c-t3)' : evt.color }} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="cal-divider" />

        <div className="cal-events-section">
          <div className="cal-events-hdr">
            <span className="cal-events-date">{fmt(selDate, { month: 'long', day: 'numeric' })}</span>
            <span className="cal-events-dow">{fmt(selDate, { weekday: 'long' })}</span>
          </div>

          <div className="cal-events-list">
            {selectedEvents.length === 0 ? (
              <div className="cal-empty">
                <div className="cal-empty-icon">📋</div>
                <div className="cal-empty-text">{t('calendar.emptyTitle')}</div>
                <div className="cal-empty-sub" style={{ whiteSpace: 'pre-line' }}>
                  {t('calendar.emptySub')}
                </div>
              </div>
            ) : (
              selectedEvents.map((evt, i) => (
                <EventCard
                  key={i}
                  event={evt}
                  onPress={() => showToast(t('calendar.fromChat'))}
                  onViewChat={
                    evt.channelId && evt.messageId && CHECKLIST_CHANNEL_SCREEN[evt.channelId]
                      ? () => navigate(CHECKLIST_CHANNEL_SCREEN[evt.channelId], { highlightMessageId: evt.messageId })
                      : null
                  }
                />
              ))
            )}
          </div>
        </div>
      </div>

      <BottomNav active="s-calendar" />
    </>
  );
}

function EventCard({ event, onPress, onViewChat }) {
  const { t, tx } = useI18n();
  // 채팅 체크리스트에서 온 일정은 항목 id 로 번역본을 찾아, 언어를 바꾸면 함께 바뀐다
  const base = `checklists.${event.checklistId}`;
  const linked = event.source === 'chat-checklist';
  const title = linked ? tx(`${base}.items.${event.checklistItemId}.text`, event.title) : event.title;
  const desc  = linked && event.desc ? tx(`${base}.items.${event.checklistItemId}.sub`, event.desc) : event.desc;
  const type  = linked ? tx(`${base}.type`, event.type) : event.type;
  const dotColor  = event.isCompleted ? 'var(--c-t3)' : event.color;
  const typeStyle = {
    color:      event.isCompleted ? 'var(--c-t3)' : event.color,
    background: event.isCompleted ? 'var(--c-bg)'  : `${event.color}18`,
  };
  return (
    <div className={`cal-event-card${event.isCompleted ? ' completed' : ''}`} onClick={onPress}>
      <div className="cal-event-bar" style={{ background: dotColor }} />
      <div className="cal-event-body">
        <div className={`cal-event-title${event.isCompleted ? ' done' : ''}`}>{title}</div>
        {desc && <div className="cal-event-desc">{desc}</div>}
        <div className="cal-event-meta">
          <span className="cal-event-type" style={typeStyle}>{type}</span>
          {event.source === 'chat-checklist' && (
            <span className="cal-event-source chat">{t('calendar.chatBadge')}</span>
          )}
          {event.isCompleted && <span className="cal-event-completed">{t('calendar.done')}</span>}
        </div>
        {onViewChat && (
          <button
            className="cal-event-chat-link"
            onClick={e => { e.stopPropagation(); onViewChat(); }}
          >
            {t('calendar.viewChat')}
          </button>
        )}
      </div>
    </div>
  );
}
