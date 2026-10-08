import { useApp } from '../../hooks/useApp';
import { SendIcon } from '../Common/icons';

/**
 * ChatInput
 *
 * props:
 *   channelId — 어느 채널의 입력창인지 (draft를 채널별로 구분해서 저장하기 위함)
 *   onSend(text) — 전송 시 입력 텍스트를 인자로 전달
 *
 * 입력 중인 텍스트는 이 컴포넌트가 들고 있지 않고 AppContext의 draft로 관리한다.
 * 그래서 다른 화면으로 이동했다가 돌아와도(=이 컴포넌트가 언마운트/재마운트돼도)
 * 작성 중이던 내용이 그대로 남아있고, 채널별 빠른 질문 버튼도 같은 draft를
 * 채워 넣는 방식으로 "입력창에 미리 채워주기"를 구현한다.
 */
export default function ChatInput({ placeholder, inputId, channelId, onSend, disabled }) {
  const { getDraft, setDraft, clearDraft } = useApp();
  const text = getDraft(channelId);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    clearDraft(channelId);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-input-bar">
      <input
        id={inputId}
        className="c-input"
        placeholder={placeholder}
        value={text}
        onChange={e => setDraft(channelId, e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button className="send-btn" onClick={handleSend} disabled={disabled}>
        <SendIcon />
      </button>
    </div>
  );
}
