/**
 * SourceModal
 * 출처 정보를 바텀 시트 모달로 표시합니다.
 *
 * Props:
 *   isOpen   : boolean
 *   onClose  : () => void
 *   sources  : Array<{ label: string, detail: string, url?: string }>
 *              url이 있으면 공식 링크를 함께 보여준다 (새 탭으로 열림)
 */
import { useI18n } from '../../i18n';

export default function SourceModal({ isOpen, onClose, sources = [] }) {
  const { t } = useI18n();
  if (!isOpen) return null;
  return (
    <div className="source-modal-overlay" onClick={onClose}>
      <div className="source-modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="source-modal-handle" />
        <div className="source-modal-title">{t('source.title')}</div>
        <div className="source-modal-list">
          {sources.map((src, i) => (
            <div key={i} className="source-modal-item">
              <div className="source-modal-label">{src.label}</div>
              {src.detail && <div className="source-modal-detail">{src.detail}</div>}
              {src.url && (
                <a className="source-modal-link" href={src.url} target="_blank" rel="noreferrer">
                  🔗 {src.url.replace(/^https?:\/\//, '')}
                </a>
              )}
            </div>
          ))}
        </div>
        <button className="source-modal-close" onClick={onClose}>{t('common.close')}</button>
      </div>
    </div>
  );
}
