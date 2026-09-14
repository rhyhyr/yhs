import { SendIcon } from './icons';

export default function ChatInput({ placeholder, inputId, onSend }) {
  return (
    <div className="chat-input-bar">
      <input
        id={inputId}
        className="c-input"
        placeholder={placeholder}
      />
      <button className="send-btn" onClick={onSend}>
        <SendIcon />
      </button>
    </div>
  );
}
