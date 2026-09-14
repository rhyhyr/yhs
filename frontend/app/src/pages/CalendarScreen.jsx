import { useState } from 'react';
import { useApp } from '../hooks/useApp';
import BottomNav from '../components/BottomNav';
import { calendarEvents, formatDateKey } from '../api/mockData';

export default function CalendarScreen() {
  const { showToast } = useApp();
  const [calDate, setCalDate] = useState(new Date(2026, 7, 1));
  const [selectedDateKey, setSelectedDateKey] = useState(null);

  const year = calDate.getFullYear();
  const month = calDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const startWeekday = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevMonthDays = new Date(year, month, 0).getDate();
  const today = new Date();

  const resolvedSelected = selectedDateKey || (() => {
    const first = Object.keys(calendarEvents).find(key => {
      const d = new Date(key);
      return d.getFullYear() === year && d.getMonth() === month;
    });
    return first || formatDateKey(year, month, 1);
  })();

  function changeMonth(diff) {
    setCalDate(prev => {
      const d = new Date(prev);
      d.setMonth(d.getMonth() + diff);
      return d;
    });
    setSelectedDateKey(null);
  }

  const selectedEvents = calendarEvents[resolvedSelected] || [];
  const [selYear, selMonth, selDay] = resolvedSelected.split('-');

  const cells = [];
  for (let i = 0; i < startWeekday; i++) {
    const dateNum = prevMonthDays - startWeekday + i + 1;
    cells.push(
      <div key={`prev-${i}`} className="cal-cell other-month">
        <div className="cal-date">{dateNum}</div>
        <div className="cal-dots" />
      </div>
    );
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const dateKey = formatDateKey(year, month, day);
    const events = calendarEvents[dateKey] || [];
    const cellDate = new Date(year, month, day);
    const isToday = today.getFullYear() === cellDate.getFullYear()
      && today.getMonth() === cellDate.getMonth()
      && today.getDate() === cellDate.getDate();
    const isSelected = resolvedSelected === dateKey;
    let cls = 'cal-cell';
    if (isToday) cls += ' today';
    if (isSelected) cls += ' selected';
    cells.push(
      <div key={`day-${day}`} className={cls} onClick={() => setSelectedDateKey(dateKey)}>
        <div className="cal-date">{day}</div>
        <div className="cal-dots">
          {events.map((evt, i) => (
            <div key={i} className="cal-dot" style={{ background: evt.color }} />
          ))}
        </div>
      </div>
    );
  }
  const totalCells = startWeekday + daysInMonth;
  const nextDays = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= nextDays; i++) {
    cells.push(
      <div key={`next-${i}`} className="cal-cell other-month">
        <div className="cal-date">{i}</div>
        <div className="cal-dots" />
      </div>
    );
  }

  return (
    <>
      <div className="topbar">
        <div className="tb-title" style={{ flex: 1 }}>캘린더</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => changeMonth(-1)} style={{ width: '30px', height: '30px', borderRadius: '9px', border: '1.5px solid var(--c-border)', background: 'var(--c-surface)', cursor: 'pointer', fontSize: '14px' }}>‹</button>
          <button onClick={() => changeMonth(1)} style={{ width: '30px', height: '30px', borderRadius: '9px', border: '1.5px solid var(--c-border)', background: 'var(--c-surface)', cursor: 'pointer', fontSize: '14px' }}>›</button>
        </div>
      </div>
      <div id="calendar-month-label" style={{ padding: '2px 14px 6px', fontSize: '13px', fontWeight: 500, color: 'var(--c-t2)' }}>
        {year}년 {month + 1}월
      </div>
      <div className="scroll-area">
        <div style={{ padding: '0 14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', marginBottom: '4px' }}>
            {['일','월','화','수','목','금','토'].map(d => (
              <div key={d} style={{ textAlign: 'center', fontSize: '11px', color: 'var(--c-t3)', fontWeight: 500, padding: '3px 0' }}>{d}</div>
            ))}
          </div>
          <div id="cal-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: '6px' }}>
            {cells}
          </div>
        </div>
        <div id="selected-date-title" style={{ padding: '14px 14px 6px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>
          {selYear}년 {Number(selMonth)}월 {Number(selDay)}일 일정
        </div>
        <div id="selected-events" style={{ padding: '0 14px 20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {selectedEvents.length === 0 ? (
            <div style={{ padding: '14px', border: '1.5px dashed var(--c-border)', borderRadius: '13px', fontSize: '13px', color: 'var(--c-t2)', background: '#FAFAF8' }}>
              이 날짜에는 등록된 일정이 없어요.
            </div>
          ) : (
            selectedEvents.map((event, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', padding: '12px 13px', border: '1.5px solid var(--c-border)', borderRadius: '13px', background: 'var(--c-surface)' }}>
                <div style={{ width: '4px', borderRadius: '2px', background: event.color, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-t1)' }}>{event.title}</div>
                  <div style={{ fontSize: '11px', color: 'var(--c-t2)', marginTop: '4px' }}>{event.desc}</div>
                  <div style={{ display: 'inline-block', marginTop: '6px', fontSize: '10px', fontWeight: 500, padding: '2px 8px', borderRadius: '8px', background: '#F5F4F0', color: 'var(--c-t2)' }}>
                    {event.type}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      <BottomNav active="s-calendar" />
    </>
  );
}
