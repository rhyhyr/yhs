import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useChatChannel } from '../../hooks/useChatChannel';
import { getChannel } from '../../api/channels';
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
import { useI18n } from '../../i18n';

const CHANNEL_ID = 'school';

export default function SchoolScreen() {
  const { navigate, back, showToast, addChatChecklistToCalendar, setDraft } = useApp();
  const { messages, isLoading, handleSend } = useChatChannel(CHANNEL_ID);
  const { t, localizeChannel } = useI18n();
  const bottomRef = useRef(null);

  const [stage, setStage]                           = useState('idle');
  const [activeChecklistId, setActiveChecklistId]   = useState(null);
  const [showModal, setShowModal]                   = useState(false);
  const [showRedirect, setShowRedirect]             = useState(false);
  const [linkedEarliestDate, setLinkedEarliestDate] = useState(null);

  const channel      = localizeChannel(getChannel(CHANNEL_ID));
  const quickActions = channel?.quickActions ?? [];

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages.length]);

  const lastAiMsg   = [...messages].reverse().find(m => m.role === 'ai');
  const lastAiMsgId = lastAiMsg?.id;
  useEffect(() => {
    if (lastAiMsg?.checklistId) {
      setStage('ask-checklist');
      setActiveChecklistId(null);
      setShowModal(false);
    }
  }, [lastAiMsgId]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleChecklistYes() {
    setActiveChecklistId(lastAiMsg.checklistId);
    setStage('ask-calendar');
  }
  function handleChecklistNo()  { setStage('done'); }
  function handleCalendarYes()  { setStage('done'); setShowModal(true); }
  function handleCalendarNo()   { setStage('done'); }

  function handleModalConfirm(selectedIds, dateOverrides) {
    const checklist = getMockChecklist(activeChecklistId);
    if (!checklist) return;
    const events = convertChecklistItemsToEvents(checklist, selectedIds, dateOverrides);
    addChatChecklistToCalendar(events);
    const earliest = Object.keys(events).sort()[0] ?? null;
    setLinkedEarliestDate(earliest);
    showToast(t('toast.calendarLinked'));
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

  // 질문형 버튼은 바로 전송하지 않고 입력창에 채워서, 사용자가 확인/수정 후 직접 전송하게 함
  function handleQuickAction(action) {
    if (action.type === 'navigate') navigate(action.target);
    else setDraft(CHANNEL_ID, action.text);
  }

  return (
    <>
      <div className="slim-header">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div className="slim-ch-icon" style={{ background: 'var(--c-green-l)' }}>🏫</div>
        <div className="slim-ch-name">{channel.name}</div>
        <div className="slim-rag">{t('common.ragActive')}</div>
      </div>

      <div className="qa-scroll">
        {activeChecklistId && (stage === 'ask-calendar' || stage === 'done') && (
          <button
            className="qa-btn qa-btn-checklist"
            onClick={() => navigate(CHECKLIST_SCREEN[activeChecklistId])}
          >
            {t('channel.checklist')}
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
        <div className="chat-area" id="school-chat-area">
          {messages.length === 0 && (
            <ChatMessage role="ai">{channel?.welcomeMsg}</ChatMessage>
          )}
          {messages.map(msg => (
            <ChatMessage key={msg.id} role={msg.role}>{msg.text}</ChatMessage>
          ))}
          {isLoading && <ChatMessage role="ai">…</ChatMessage>}

          {stage === 'ask-checklist' && lastAiMsg?.checklistId && (
            <ChecklistAskCard
              checklistId={lastAiMsg.checklistId}
              onConfirm={handleChecklistYes}
              onDismiss={handleChecklistNo}
            />
          )}

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
        inputId="school-input"
        channelId={CHANNEL_ID}
        placeholder={channel.placeholder}
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
