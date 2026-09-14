import { useState, useEffect, useMemo } from 'react';
import { useApp } from '../../hooks/useApp';
import { getCalendarEvents, mergeEvents } from '../../api/calendar';
import { formatDateKey } from '../../api/mockData';
import BottomNav from '../../components/Common/BottomNav';

const WEEK_KO = ['일', '월', '화', '수', '목', '금', '토'];

export default function CalendarScreen() {
  const { showToast, chatCalendarItems, navParams } = useApp();
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
  const selDow = WEEK_KO[new Date(selY, selM - 1, selD).getDay()];

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
        <div className="tb-title" style={{ flex: 1 }}>캘린더</div>
        <div className="cal-nav-group">
          <button className="cal-today-btn" onClick={goToday}>오늘</button>
          <button className="cal-nav-btn" onClick={() => changeMonth(-1)}>‹</button>
          <button className="cal-nav-btn" onClick={() => changeMonth(1)}>›</button>
        </div>
      </div>

      <div className="scroll-area">
        <div className="cal-month-label">{year}년 {month + 1}월</div>

        <div className="cal-weekdays">
          {WEEK_KO.map((d, i) => (
            <div key={d} className={`cal-weekday${i === 0 ? ' sun' : i === 6 ? ' sat' : ''}`}>{d}</div>
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
            <span className="cal-events-date">{selM}월 {selD}일</span>
            <span className="cal-events-dow">{selDow}요일</span>
          </div>

          <div className="cal-events-list">
            {selectedEvents.length === 0 ? (
              <div className="cal-empty">
                <div className="cal-empty-icon">📋</div>
                <div className="cal-empty-text">등록된 일정이 없어요</div>
                <div className="cal-empty-sub">
                  채팅에서 체크리스트를 만들고<br />캘린더에 연동해 보세요
                </div>
              </div>
            ) : (
              selectedEvents.map((evt, i) => (
                <EventCard
                  key={i}
                  event={evt}
                  onPress={() => showToast('채팅에서 등록한 일정이에요')}
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

function EventCard({ event, onPress }) {
  const dotColor  = event.isCompleted ? 'var(--c-t3)' : event.color;
  const typeStyle = {
    color:      event.isCompleted ? 'var(--c-t3)' : event.color,
    background: event.isCompleted ? 'var(--c-bg)'  : `${event.color}18`,
  };
  return (
    <div className={`cal-event-card${event.isCompleted ? ' completed' : ''}`} onClick={onPress}>
      <div className="cal-event-bar" style={{ background: dotColor }} />
      <div className="cal-event-body">
        <div className={`cal-event-title${event.isCompleted ? ' done' : ''}`}>{event.title}</div>
        {event.desc && <div className="cal-event-desc">{event.desc}</div>}
        <div className="cal-event-meta">
          <span className="cal-event-type" style={typeStyle}>{event.type}</span>
          {event.source === 'chat-checklist' && (
            <span className="cal-event-source chat">💬 채팅</span>
          )}
          {event.isCompleted && <span className="cal-event-completed">완료</span>}
        </div>
      </div>
    </div>
  );
}
