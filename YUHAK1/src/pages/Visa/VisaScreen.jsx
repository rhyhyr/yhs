import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import { getChannel } from '../../api/channels';
import { getVisaInfo } from '../../api/user';
import { getMockChecklist } from '../../data/mockChecklistData';
import { convertChecklistItemsToEvents } from '../../api/calendar';
import { BackIcon } from '../../components/Common/icons';
import ChatInput from '../../components/Chat/ChatInput';
import ChatMessage from '../../components/Chat/ChatMessage';
import ChecklistAskCard from '../../components/Chat/ChecklistAskCard';
import { CHECKLIST_SCREEN } from '../../data/mockChecklistData';
import CalendarLinkCard from '../../components/Chat/CalendarLinkCard';
import CalendarRedirectCard from '../../components/Chat/CalendarRedirectCard';
import ChecklistSelectModal from '../../components/Chat/ChecklistSelectModal';

const CHANNEL_ID = 'visa';

// 플로우 단계
// 'idle' → 'ask-checklist' → 'checklist-created' → 'ask-calendar' → 'done'

export default function VisaScreen() {
  const { navigate, back, infoOpen, setInfoOpen, showToast, addChatChecklistToCalendar } = useApp();
  const { messages, isLoading, handleSend } = useChatChannel(CHANNEL_ID);
  const bottomRef = useRef(null);
  const [visa, setVisa] = useState(null);

  // ── 플로우 상태 ────────────────────────────────────────────
  const [stage, setStage]                         = useState('idle');
  const [activeChecklistId, setActiveChecklistId] = useState(null);
  const [showModal, setShowModal]                 = useState(false);
  const [showRedirect, setShowRedirect]           = useState(false);
  const [linkedEarliestDate, setLinkedEarliestDate] = useState(null);

  const channel      = getChannel(CHANNEL_ID);
  const quickActions = channel?.quickActions ?? [];

  useEffect(() => { getVisaInfo().then(setVisa).catch(() => {}); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages.length]);

  // 새 AI 메시지가 올 때마다 플로우 리셋
  const lastAiMsg   = [...messages].reverse().find(m => m.role === 'ai');
  const lastAiMsgId = lastAiMsg?.id;
  useEffect(() => {
    if (lastAiMsg?.checklistId) {
      setStage('ask-checklist');
      setActiveChecklistId(null);
      setShowModal(false);
    }
  }, [lastAiMsgId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 핸들러 ────────────────────────────────────────────────
  function handleChecklistYes() {
    setActiveChecklistId(lastAiMsg.checklistId);
    setStage('ask-calendar');
  }
  function handleChecklistNo() {
    setStage('done');
  }
  function handleCalendarYes() {
    setStage('done');
    setShowModal(true);
  }
  function handleCalendarNo() {
    setStage('done');
  }
  function handleModalConfirm(selectedIds) {
    const checklist = getMockChecklist(activeChecklistId);
    if (!checklist) return;
    const events = convertChecklistItemsToEvents(checklist, selectedIds);
    addChatChecklistToCalendar(events);
    const earliest = Object.keys(events).sort()[0] ?? null;
    setLinkedEarliestDate(earliest);
    showToast('📅 연동되었습니다!');
    setShowModal(false);
    setShowRedirect(true);
  }

  function handleRedirectYes() {
    setShowRedirect(false);
    navigate('s-calendar', { targetDate: linkedEarliestDate });
  }

  function handleRedirectNo() {
    setShowRedirect(false);
  }

  const dDay        = visa?.dDay        ?? '87';
  const expiryLabel = visa?.expiryLabel ?? '2026. 8. 15';
  const visaType    = visa?.type        ?? 'D-2';

  function handleQuickAction(action) {
    if (action.type === 'navigate') navigate(action.target);
    else handleSend(action.text);
  }

  return (
    <>
      <div className="slim-header">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
        <div className="slim-ch-name">비자 &amp; 체류</div>
        <div className="slim-rag">RAG 활성</div>
        <div className="slim-d87" style={{ opacity: 0.5 }} onClick={() => setInfoOpen(o => !o)}>
          <span id="d87-txt">D-{dDay}</span>
          <span style={{ fontSize: '10px' }}>{infoOpen ? '▾' : '▸'}</span>
        </div>
      </div>

      {infoOpen && (
        <div className="info-panel" style={{ opacity: 0.55 }}>
          <div className="i-chip">🗓 {visaType} 만료 <strong>{expiryLabel}</strong></div>
          <div className="i-chip green">🔔 알림 설정됨</div>
          <span className="ghost-badge" style={{ alignSelf: 'center' }}>예시</span>
        </div>
      )}

      <div className="qa-scroll">
        {activeChecklistId && (stage === 'ask-calendar' || stage === 'done') && (
          <button
            className="qa-btn qa-btn-checklist"
            onClick={() => navigate(CHECKLIST_SCREEN[activeChecklistId])}
          >
            📋 체크리스트
          </button>
        )}
        {quickActions.map(action => (
          <button key={action.label} className="qa-btn"
            onClick={() => handleQuickAction(action)} disabled={isLoading}>
            {action.label}
          </button>
        ))}
      </div>

      <div className="scroll-area">
        <div className="chat-area" id="visa-chat-area">
          {messages.length === 0 && (
            <ChatMessage role="ai">{channel?.welcomeMsg}</ChatMessage>
          )}
          {messages.map(msg => (
            <ChatMessage key={msg.id} role={msg.role}>{msg.text}</ChatMessage>
          ))}
          {isLoading && <ChatMessage role="ai">…</ChatMessage>}

          {/* 1단계: 체크리스트 만들까요? */}
          {stage === 'ask-checklist' && lastAiMsg?.checklistId && (
            <ChecklistAskCard
              checklistId={lastAiMsg.checklistId}
              onConfirm={handleChecklistYes}
              onDismiss={handleChecklistNo}
            />
          )}

          {/* 2단계: 체크리스트 인라인 표시 + 캘린더 연동 질문 */}
          {stage === 'ask-calendar' && (
            <CalendarLinkCard
              onConfirm={handleCalendarYes}
              onDismiss={handleCalendarNo}
            />
          )}

          {showRedirect && (
            <CalendarRedirectCard
              onConfirm={handleRedirectYes}
              onDismiss={handleRedirectNo}
            />
          )}

          <div ref={bottomRef} />
        </div>
        <div style={{ height: '8px' }} />
      </div>

      <ChatInput
        inputId="visa-input"
        placeholder={channel?.placeholder ?? '비자 관련 질문하기...'}
        onSend={handleSend}
        disabled={isLoading}
      />

      {showModal && activeChecklistId && (
        <ChecklistSelectModal
          checklistId={activeChecklistId}
          onConfirm={handleModalConfirm}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}
