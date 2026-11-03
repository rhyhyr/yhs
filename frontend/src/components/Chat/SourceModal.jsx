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

/**
 * 링크에 보여줄 글자
 * - '/sources/12_…pdf' (서버에 올린 원문 PDF) → '원문 PDF 보기'
 * - 웹 주소 → 'www.hikorea.go.kr/…' 처럼 사람이 읽을 수 있게 (퍼센트 인코딩 풀기)
 */
function linkText(url, t) {
  if (url.startsWith('/sources/')) return t('source.openPdf');
  let text = url.replace(/^https?:\/\//, '');
  try { text = decodeURI(text); } catch { /* 잘못된 인코딩이면 그대로 */ }
  return text.length > 60 ? `${text.slice(0, 57)}…` : text;
}

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
                  {src.url.startsWith('/sources/') ? '📄' : '🔗'} {linkText(src.url, t)}
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
