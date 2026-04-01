/**
 * ChatMessage
 * role: 'ai' | 'user'
 * children: 메시지 내용 (텍스트 또는 JSX)
 * style: bubble에 추가할 인라인 스타일 (선택)
 */
export default function ChatMessage({ role, children, style }) {
  if (role === 'user') {
    return (
      <div className="msg-user">
        <div className="bubble-user">{children}</div>
      </div>
    );
  }
  return (
    <div className="msg-ai">
      <div className="ai-av">AI</div>
      <div className="bubble-ai" style={style}>{children}</div>
    </div>
  );
}
