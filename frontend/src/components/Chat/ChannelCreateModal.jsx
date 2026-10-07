import { useI18n } from '../../i18n';

/**
 * ChannelCreateModal
 *
 * "OO 채널을 생성할까요?" 확인 바텀시트.
 * ChatScreen(메인채팅 카테고리 칩)과 HomeScreen(예시 채널 카드)이
 * 같은 채널 생성 흐름을 타므로 모달 UI를 여기 하나로 공유한다.
 *
 * props:
 *   icon       — 채널 이모지
 *   name       — 화면에 보여줄 채널 이름 (이미 현재 언어로 번역된 값)
 *   onConfirm  — "채널 생성하기" 클릭
 *   onClose    — "나중에"/바깥 클릭으로 닫기
 */
export default function ChannelCreateModal({ icon, name, onConfirm, onClose }) {
  const { t } = useI18n();
  return (
    <div className="source-modal-overlay" onClick={onClose}>
      <div className="channel-modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="source-modal-handle" />
        <div style={{ textAlign: 'center', padding: '4px 0 8px' }}>
          <div style={{ fontSize: '36px', marginBottom: '10px' }}>{icon}</div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--c-t1)', marginBottom: '6px' }}>
            {t('chat.createTitle', { name })}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--c-t2)', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
            {t('chat.createDesc')}
          </div>
        </div>
        <button className="channel-modal-btn primary" onClick={onConfirm}>
          {t('chat.createBtn')}
        </button>
        <button className="channel-modal-btn secondary" onClick={onClose}>
          {t('chat.later')}
        </button>
      </div>
    </div>
  );
}
