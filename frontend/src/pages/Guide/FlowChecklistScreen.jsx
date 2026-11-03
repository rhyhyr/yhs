import { useMemo, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { BackIcon } from '../../components/Common/icons';
import { useI18n } from '../../i18n';
import { GUIDE_FLOWS } from '../../data/guideFlows';
import ChecklistSelectModal from '../../components/Chat/ChecklistSelectModal';
import { convertChecklistItemsToEvents } from '../../api/calendar';
import { fromToday } from '../../utils/demoDates';

// 캘린더에 넣을 때 기본 날짜: 첫 항목은 3일 뒤, 그 뒤로 2일 간격 (시트에서 ✏️로 바꿀 수 있음)
const FIRST_DUE_IN_DAYS = 3;
const DUE_GAP_DAYS = 2;

/**
 * 선택형 안내 트리(data/guideFlows.js)의 마지막 단계 체크리스트.
 * navParams { flow, node } 로 어떤 가지인지 받아, 그 가지의 항목을 그린다.
 *
 * 체크 상태는 다른 체크리스트 화면들과 같이 메모리에만 둔다 — 화면이 계속
 * 마운트돼 있어서 앱을 새로고침하기 전까지는 가지별로 유지된다.
 *
 * 하단 "캘린더에 일정으로 등록" → 항목·날짜를 고르는 시트(ChecklistSelectModal)
 * → 앱 캘린더에 등록(구글 캘린더 연결 시 거기도 바로 등록 가능) → 캘린더 화면으로 이동.
 */
export default function FlowChecklistScreen() {
  const { back, navigate, navParams, addChatChecklistToCalendar, showToast } = useApp();
  const { t } = useI18n();
  const [checked, setChecked] = useState({});
  const [calOpen, setCalOpen] = useState(false);

  const checklist = GUIDE_FLOWS[navParams?.flow]?.nodes[navParams?.node]?.checklist;

  // 캘린더 시트용 체크리스트 — 그룹을 펼치고 항목마다 기본 날짜를 붙인다
  const calChecklist = useMemo(() => {
    if (!checklist) return null;
    const items = checklist.groups.flatMap(g => g.items).map((item, i) => ({
      id: i + 1,
      text: item.text,
      sub: item.sub ?? '',
      dueDate: fromToday(FIRST_DUE_IN_DAYS + i * DUE_GAP_DAYS),
    }));
    return {
      id: `flow-${navParams.flow}-${navParams.node}`,
      title: checklist.title,
      type: checklist.title.split(' — ')[0],
      color: '#5B45C2',
      items,
    };
  }, [checklist, navParams?.flow, navParams?.node]);

  if (!checklist) return null;

  function handleCalendarConfirm(selectedIds, dateOverrides) {
    const events = convertChecklistItemsToEvents(calChecklist, selectedIds, dateOverrides, { channelId: 'visa' });
    addChatChecklistToCalendar(events);
    setCalOpen(false);
    showToast(t('toast.calendarLinked'));
    navigate('s-calendar', { targetDate: Object.keys(events).sort()[0] ?? null });
  }

  const prefix = `${navParams.flow}/${navParams.node}/`;
  const keyOf = (gi, ii) => `${prefix}${gi}.${ii}`;
  const all = checklist.groups.flatMap((g, gi) => g.items.map((_, ii) => keyOf(gi, ii)));
  const done = all.filter(k => checked[k]).length;
  const pct = Math.round(done / all.length * 100);
  const current = all.find(k => !checked[k]);
  const toggle = k => setChecked(c => ({ ...c, [k]: !c[k] }));

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
          {t('visa.backToChannel')}
        </div>
      </div>

      <div style={{ padding: '12px 16px 4px' }}>
        <div className="tb-title" style={{ fontSize: '17px' }}>{checklist.title}</div>
        <div className="tb-sub">{checklist.sub}</div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bg">
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="prog-label">
          <span>{t('guide.progress', { done, total: all.length })}</span>
          <span style={{ color: 'var(--c-green)' }}>{pct}%</span>
        </div>
      </div>

      <div className="scroll-area" style={{ paddingBottom: '12px' }}>
        {checklist.groups.map((g, gi) => (
          <div key={g.title} className="step-card">
            <div className="step-card-hdr">
              <span>{g.title}</span>
              <span style={{ fontSize: '11px', fontWeight: 400 }}>
                {t('guide.groupProgress', { done: g.items.filter((_, ii) => checked[keyOf(gi, ii)]).length, total: g.items.length })}
              </span>
            </div>
            {g.items.map((item, ii) => {
              const k = keyOf(gi, ii);
              const on = !!checked[k];
              const dim = !on && k !== current ? { color: 'var(--c-t3)' } : {};
              return (
                <div key={k} className="step-row" onClick={() => toggle(k)}>
                  <div className={`step-cb${on ? ' checked' : k === current ? ' current' : ''}`}>
                    {on ? '✓' : ''}
                  </div>
                  <div className="step-label">
                    <div className={`step-text${on ? ' done' : ''}`} style={dim}>{item.text}</div>
                    {item.sub && <div className={`step-sub${on ? ' done' : ''}`} style={dim}>{item.sub}</div>}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
        <button className="cta-primary flow-cal-btn" onClick={() => setCalOpen(true)}>
          📅 {t('checklist.addToCalendar')}
        </button>
      </div>

      {calOpen && (
        <ChecklistSelectModal
          checklist={calChecklist}
          onConfirm={handleCalendarConfirm}
          onClose={() => setCalOpen(false)}
        />
      )}
    </>
  );
}
