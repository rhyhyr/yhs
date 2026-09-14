import { useState } from 'react';
import { SendIcon } from '../Common/icons';

/**
 * ChatInput
 * onSend(text) — 전송 시 입력 텍스트를 인자로 전달
 */
export default function ChatInput({ placeholder, inputId, onSend, disabled }) {
  const [text, setText] = useState('');

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
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
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button className="send-btn" onClick={handleSend} disabled={disabled}>
        <SendIcon />
      </button>
    </div>
  );
}
