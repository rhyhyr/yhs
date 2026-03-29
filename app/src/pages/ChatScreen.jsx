import { useApp } from '../hooks/useApp';
import { BackIcon } from '../components/icons';
import BottomNav from '../components/BottomNav';
import ChatInput from '../components/ChatInput';
import ChatMessage from '../components/ChatMessage';

export default function ChatScreen() {
  const { navigate, back, showToast } = useApp();
  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}>
          <BackIcon />
        </div>
        <div>
          <div className="tb-title">메인 채팅</div>
          <div className="tb-sub">모든 채널에 질문하기</div>
        </div>
      </div>
      <div className="scroll-area">
        <div style={{ padding: '10px 14px 6px', fontSize: '11px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.6px', textTransform: 'uppercase' }}>
          케이스 A · 1차 답변 가능
        </div>
        <div className="chat-area" style={{ paddingTop: '4px' }}>
          <ChatMessage role="user">외국인은 알바 어떻게 해요?</ChatMessage>
        </div>
        <div className="ans-wrap">
          <div className="ans-domain" style={{ background: 'var(--c-amber-l)' }}>
            <div className="ans-dot" style={{ background: 'var(--c-amber)' }} />
            <span style={{ color: 'var(--c-amber)', fontWeight: 600 }}>취업 &amp; 아르바이트</span>
          </div>
          <div className="ans-body">D-2 유학생은 <strong>시간제 취업 허가</strong> 후 주 20시간 이내 알바 가능합니다.</div>
          <div className="ans-tags">
            <span className="tag" style={{ background: 'var(--c-amber-l)', color: 'var(--c-amber)' }}>#취업</span>
            <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#비자</span>
          </div>
        </div>
        <div className="cta-card" onClick={() => navigate('s-channel-main')} style={{ marginTop: '8px' }}>
          <div className="cta-icon" style={{ background: 'var(--c-amber-l)' }}>💼</div>
          <div className="cta-body">
            <div className="cta-title">채널에서 자세히 보기</div>
            <div className="cta-sub">허가 절차 · 학교 규정 · Step-by-step</div>
          </div>
          <div className="cta-arrow">›</div>
        </div>

        <div style={{ margin: '16px 14px 10px', height: '1px', background: 'var(--c-border)' }} />

        <div style={{ padding: '0 14px 6px', fontSize: '11px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.6px', textTransform: 'uppercase' }}>
          케이스 B · 1차 답변 불가
        </div>
        <div className="chat-area" style={{ paddingTop: '4px' }}>
          <ChatMessage role="user">건강보험 외국인 특례 3조 내용이 뭐예요?</ChatMessage>
          <ChatMessage role="ai" style={{ color: 'var(--c-t2)', fontSize: '13px' }}>
            이 질문은 <strong style={{ color: 'var(--c-t1)' }}>병원 &amp; 보험</strong> 채널에서 정확하게 답변드릴 수 있어요.
          </ChatMessage>
        </div>
        <div className="cta-card neutral" onClick={() => showToast('병원 & 보험 채널로 이동합니다')}>
          <div className="cta-icon" style={{ background: '#FEE2E2' }}>🏥</div>
          <div className="cta-body">
            <div className="cta-title">병원 &amp; 보험 채널에서 답변 받기</div>
            <div className="cta-sub">건강보험 전용 RAG로 정확한 답변</div>
          </div>
          <div className="cta-arrow">›</div>
        </div>
        <div id="main-chat-area" className="chat-area" style={{ paddingTop: 0 }} />
        <div style={{ height: '16px' }} />
      </div>
      <ChatInput
        inputId="main-input"
        placeholder="무엇이든 질문하세요..."
        onSend={() => showToast('메시지를 전송합니다')}
      />
      <BottomNav active="s-main" />
    </>
  );
}
