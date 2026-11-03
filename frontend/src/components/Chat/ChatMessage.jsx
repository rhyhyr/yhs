/**
 * ChatMessage
 * role: 'ai' | 'user'
 * children: 메시지 내용 (텍스트 또는 JSX)
 * style: bubble에 추가할 인라인 스타일 (선택)
 */

// 본문 인용 형식: [문서명, p.N] / [문서명.pdf, 3페이지] 등
const CITATION_RE = /\[([^\]\n]+,\s*(?:p\.?\s*)?\d+\s*(?:페이지)?)\]/g;

/** 문서명 비교용 정규화 — '12_하이코리아_체류기간연장허가.pdf' 와 '하이코리아 체류기간연장허가' 를 같게 본다 */
function normalizeDoc(name) {
  return (name || '').replace(/\.pdf$/i, '').replace(/^\d+_/, '').replace(/[\s_·]/g, '').toLowerCase();
}

function parseCitation(citation) {
  const page = (citation.match(/(?:p\.?\s*|페이지\s*)(\d+)/i) || citation.match(/(\d+)\s*$/))?.[1];
  const doc = normalizeDoc(citation.slice(0, citation.lastIndexOf(',')).trim());
  return { page, doc };
}

/** 인용 하나에 해당하는 출처 찾기 — 문서명+페이지 → 문서명 → (마지막 수단) 페이지 순 */
function findSource(sources, citation) {
  const { page, doc } = parseCitation(citation);
  const sameDoc = item => {
    const label = normalizeDoc(item.label);
    return doc && label && (label.includes(doc) || doc.includes(label));
  };
  const samePage = item => item.detail?.match(/p\.(\d+)/i)?.[1] === page;
  return sources.find(item => sameDoc(item) && samePage(item))
    || sources.find(sameDoc)
    || sources.find(samePage);
}

/** 본문에 인용된 문서를 앞으로 — 출처 줄 첫 문서가 실제 근거 문서가 되도록 */
function citedFirst(sources, text) {
  if (typeof text !== 'string' || sources.length < 2) return sources;
  const cited = [];
  for (const m of text.matchAll(CITATION_RE)) {
    const { doc } = parseCitation(m[1]);
    const hit = doc && sources.find(item => {
      const label = normalizeDoc(item.label);
      return label && (label.includes(doc) || doc.includes(label));
    });
    if (hit && !cited.includes(hit)) cited.push(hit);
  }
  return [...cited, ...sources.filter(s => !cited.includes(s))];
}

/** [문서명, p.N] 인용을 해당 출처 링크로 바꾼다 */
function linkCitations(text, sources, keyPrefix) {
  if (!sources.length) return text;
  const parts = [];
  let lastIndex = 0;
  for (const match of text.matchAll(CITATION_RE)) {
    parts.push(text.slice(lastIndex, match.index));
    const citation = match[1];
    const source = findSource(sources, citation);
    parts.push(source?.url
      ? <a key={`${keyPrefix}-c${match.index}`} href={source.url} target="_blank" rel="noreferrer">[{citation}]</a>
      : `[${citation}]`);
    lastIndex = match.index + match[0].length;
  }
  if (!parts.length) return text;
  parts.push(text.slice(lastIndex));
  return parts;
}

/** 한 줄 안의 [문서명, p.N] 인용을 출처 링크로 */
function renderInline(text, sources) {
  if (typeof text !== 'string') return text;
  return linkCitations(text, sources, 't');
}

/**
 * AI 응답 텍스트를 파싱해 구조화된 JSX로 변환
 * - "1. 내용"  → 번호 뱃지 + 텍스트
 * - "- 내용"   → 불릿 + 텍스트
 * - "#태그..."  → 태그 칩 모음
 * - "제목:"    → 볼드 섹션 헤더
 * - 빈 줄      → 간격
 */
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
  const orderedSources = citedFirst(sources, children);
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
        {orderedSources.length > 0 && onSourcesClick && (
          <button className="msg-sources" onClick={() => onSourcesClick(orderedSources)}>
            <span className="msg-sources-icon">📎</span>
            <span className="msg-sources-label">{orderedSources[0].label}</span>
            {orderedSources.length > 1 && <span className="msg-sources-more">+{orderedSources.length - 1}</span>}
            <span className="msg-sources-arrow">›</span>
          </button>
        )}
      </div>
    </div>
  );
}
