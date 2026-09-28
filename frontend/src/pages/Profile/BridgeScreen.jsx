import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';

export default function BridgeScreen() {
  const { navigate } = useApp();
  const { t } = useI18n();

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '0 24px',
      background: 'var(--c-surface)',
      gap: '0',
    }}>

      {/* 일러스트 영역 */}
      <div style={{ fontSize: '64px', marginBottom: '24px', lineHeight: 1 }}>💬</div>

      {/* 제목 */}
      <div style={{
        fontSize: '20px',
        fontWeight: 800,
        color: 'var(--c-t1)',
        textAlign: 'center',
        letterSpacing: '-.4px',
        lineHeight: 1.4,
        marginBottom: '14px',
        whiteSpace: 'pre-line',
      }}>
        {t('bridge.title')}
      </div>

      {/* 설명 */}
      <div style={{
        fontSize: '14px',
        color: 'var(--c-t2)',
        textAlign: 'center',
        lineHeight: 1.75,
        marginBottom: '32px',
        whiteSpace: 'pre-line',
      }}>
        {t('bridge.desc')}
      </div>

      {/* 기능 힌트 카드 3개 */}
      <div style={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        marginBottom: '32px',
      }}>
        {[
          { icon: '🛂', label: t('bridge.hint1') },
          { icon: '🏫', label: t('bridge.hint2') },
          { icon: '💼', label: t('bridge.hint3') },
        ].map(({ icon, label }) => (
          <div key={label} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 14px',
            background: 'var(--c-bg)',
            borderRadius: '13px',
            fontSize: '13px',
            color: 'var(--c-t1)',
            fontWeight: 500,
          }}>
            <span style={{ fontSize: '20px' }}>{icon}</span>
            {label}
          </div>
        ))}
      </div>

      {/* 메인 버튼 */}
      <button
        onClick={() => navigate('s-main')}
        style={{
          width: '100%',
          padding: '15px',
          background: 'var(--c-accent)',
          color: '#fff',
          border: 'none',
          borderRadius: '14px',
          fontSize: '16px',
          fontWeight: 700,
          fontFamily: 'inherit',
          cursor: 'pointer',
          marginBottom: '12px',
          letterSpacing: '-.2px',
        }}
      >
        {t('bridge.start')}
      </button>

      {/* 보조 버튼 */}
      <button
        onClick={() => navigate('s-home')}
        style={{
          width: '100%',
          padding: '13px',
          background: 'transparent',
          color: 'var(--c-t2)',
          border: 'none',
          borderRadius: '14px',
          fontSize: '14px',
          fontWeight: 500,
          fontFamily: 'inherit',
          cursor: 'pointer',
        }}
      >
        {t('bridge.home')}
      </button>
    </div>
  );
}
