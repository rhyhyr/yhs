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
function renderInline(text, sources) {
  if (!sources.length || typeof text !== 'string') return text;

  const citationPattern = /\[([^\]\n]+,\s*(?:p\.?\s*)?\d+\s*(?:페이지)?)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    parts.push(text.slice(lastIndex, match.index));
    const citation = match[1];
    const pageMatch = citation.match(/(?:p\.?\s*|페이지\s*)(\d+)/i) || citation.match(/(\d+)\s*$/);
    const page = pageMatch?.[1];
    const documentName = citation.slice(0, citation.lastIndexOf(',')).trim().replace(/\.pdf$/i, '');
    const source = sources.find((item) => {
      const label = (item.label || '').replace(/\.pdf$/i, '');
      const sourcePage = item.detail?.match(/p\.(\d+)/i)?.[1];
      return page === sourcePage && (label.includes(documentName) || documentName.includes(label));
    }) || sources.find((item) => item.detail?.match(/p\.(\d+)/i)?.[1] === page);

    if (source?.url) {
      parts.push(
        <a key={`citation-${match.index}`} href={source.url} target="_blank" rel="noreferrer">
          [{citation}]
        </a>
      );
    } else {
      parts.push(`[${citation}]`);
    }
    lastIndex = citationPattern.lastIndex;
  }

  if (!parts.length) return text;
  parts.push(text.slice(lastIndex));
  return parts;
}

function renderContent(text, sources) {
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
          <span>{renderInline(numMatch[2], sources)}</span>
        </div>
      );
      continue;
    }

    // "- 내용" 형식
    if (t.startsWith('- ')) {
      nodes.push(
        <div key={k++} className="msg-bullet">
          <span className="msg-bullet-dot">•</span>
          <span>{renderInline(t.slice(2), sources)}</span>
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
    nodes.push(<p key={k++} className="msg-line">{renderInline(t, sources)}</p>);
  }

  return nodes;
}

/**
 * sources: 답변 근거 출처 [{ label, detail, url }]
 *   - 본문 속 [문서명, p.N] 인용은 url 이 있는 출처와 맞춰 링크로 바꾼다
 *   - 말풍선 아래에 '📎 문서명 +N' 한 줄로 보여주고, 누르면 onSourcesClick (SourceModal)
 */
export default function ChatMessage({ role, children, style, path, sources = [], onSourcesClick }) {
  if (role === 'user') {
    return (
      <div className="msg-user">
        <div className="bubble-user">{children}</div>
      </div>
    );
  }
  const linkedSources = sources.filter((source) =>
    source.url?.startsWith('/sources/') || source.url?.startsWith('https://')
  );
  return (
    <div className="msg-ai">
      <div className="ai-av">AI</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {path && (
          <span className={`path-badge path-badge--${path}`}>
            {path === 'fast' ? '⚡ FAST' : '🔍 DEEP'}
          </span>
        )}
        <div className="bubble-ai" style={style}>{renderContent(children, linkedSources)}</div>
        {sources.length > 0 && onSourcesClick && (
          <button className="msg-sources" onClick={() => onSourcesClick(sources)}>
            <span className="msg-sources-icon">📎</span>
            <span className="msg-sources-label">{sources[0].label}</span>
            {sources.length > 1 && <span className="msg-sources-more">+{sources.length - 1}</span>}
            <span className="msg-sources-arrow">›</span>
          </button>
        )}
      </div>
    </div>
  );
}
