/**
 * ChatMessage
 * role: 'ai' | 'user'
 * children: 메시지 내용 (텍스트 또는 JSX)
 * style: bubble에 추가할 인라인 스타일 (선택)
 */

/**
 * AI 응답 텍스트를 파싱해 구조화된 JSX로 변환
 * - "1. 내용"  → 번호 뱃지 + 텍스트
 * - "- 내용"   → 불릿 + 텍스트
 * - "#태그..."  → 태그 칩 모음
 * - "제목:"    → 볼드 섹션 헤더
 * - 빈 줄      → 간격
 */
function renderContent(text) {
  if (typeof text !== 'string') return text;

  const lines = text.split('\n');
  const nodes = [];
  let k = 0;

  for (const line of lines) {
    const t = line.trim();

    if (!t) {
      nodes.push(<div key={k++} className="msg-spacer" />);
      continue;
    }

    // "1. 내용" 형식
    const numMatch = t.match(/^(\d+)\.\s+(.+)/);
    if (numMatch) {
      nodes.push(
        <div key={k++} className="msg-step">
          <span className="msg-step-num">{numMatch[1]}</span>
          <span>{numMatch[2]}</span>
        </div>
      );
      continue;
    }

    // "- 내용" 형식
    if (t.startsWith('- ')) {
      nodes.push(
        <div key={k++} className="msg-bullet">
          <span className="msg-bullet-dot">•</span>
          <span>{t.slice(2)}</span>
        </div>
      );
      continue;
    }

    // "#태그 #태그" 형식 (모든 단어가 #으로 시작)
    if (t.startsWith('#') && t.split(/\s+/).every(w => w.startsWith('#'))) {
      const tags = t.split(/\s+/).filter(Boolean);
      nodes.push(
        <div key={k++} className="msg-tags">
          {tags.map((tag, i) => (
            <span key={i} className="msg-tag">{tag}</span>
          ))}
        </div>
      );
      continue;
    }

    // "제목:" 형식 (섹션 헤더)
    if (t.endsWith(':')) {
      nodes.push(<div key={k++} className="msg-section">{t}</div>);
      continue;
    }

    // 일반 텍스트
    nodes.push(<p key={k++} className="msg-line">{t}</p>);
  }

  return nodes;
}

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
      <div className="bubble-ai" style={style}>{renderContent(children)}</div>
    </div>
  );
}
