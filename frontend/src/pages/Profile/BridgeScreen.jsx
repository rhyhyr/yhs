import { useApp } from '../../hooks/useApp';

export default function BridgeScreen() {
  const { navigate } = useApp();

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
      }}>
        이제 궁금한 것을<br />바로 물어볼 수 있어요
      </div>

      {/* 설명 */}
      <div style={{
        fontSize: '14px',
        color: 'var(--c-t2)',
        textAlign: 'center',
        lineHeight: 1.75,
        marginBottom: '32px',
      }}>
        비자, 학교생활, 주거, 아르바이트 등<br />
        궁금한 내용을 메인채팅에서 바로 시작할 수 있어요.<br />
        질문을 시작하면 필요한 채널도 함께 만들어드릴게요.
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
          { icon: '🛂', label: '비자 & 체류 관련 질문' },
          { icon: '🏫', label: '학교생활, 수강신청, 기숙사' },
          { icon: '💼', label: '취업 허가, 아르바이트 규정' },
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
        메인채팅 시작하기 →
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
        홈 먼저 보기
      </button>
    </div>
  );
}
