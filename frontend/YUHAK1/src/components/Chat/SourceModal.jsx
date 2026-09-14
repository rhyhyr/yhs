/**
 * SourceModal
 * 출처 정보를 바텀 시트 모달로 표시합니다.
 *
 * Props:
 *   isOpen   : boolean
 *   onClose  : () => void
 *   sources  : Array<{ label: string, detail: string }>
 */
export default function SourceModal({ isOpen, onClose, sources = [] }) {
  if (!isOpen) return null;
  return (
    <div className="source-modal-overlay" onClick={onClose}>
      <div className="source-modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="source-modal-handle" />
        <div className="source-modal-title">📎 출처</div>
        <div className="source-modal-list">
          {sources.map((src, i) => (
            <div key={i} className="source-modal-item">
              <div className="source-modal-label">{src.label}</div>
              <div className="source-modal-detail">{src.detail}</div>
            </div>
          ))}
        </div>
        <button className="source-modal-close" onClick={onClose}>닫기</button>
      </div>
    </div>
  );
}
