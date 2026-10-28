import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { SendIcon, MicIcon } from '../Common/icons';
import { STT_READY, recognizeSpeech } from '../../utils/speechToText';

/**
 * ChatInput
 *
 * props:
 *   channelId — 어느 채널의 입력창인지 (draft를 채널별로 구분해서 저장하기 위함)
 *   onSend(text) — 전송 시 입력 텍스트를 인자로 전달
 *
 * 🎙️ 버튼: utils/speechToText.js 를 호출해 인식된 문장을 입력창에 채운다 (전송은 사용자가 직접).
 * STT 가 아직 연결 전이면 안내 토스트만 띄운다.
 *
 * 입력 중인 텍스트는 이 컴포넌트가 들고 있지 않고 AppContext의 draft로 관리한다.
 * 그래서 다른 화면으로 이동했다가 돌아와도(=이 컴포넌트가 언마운트/재마운트돼도)
 * 작성 중이던 내용이 그대로 남아있고, 채널별 빠른 질문 버튼도 같은 draft를
 * 채워 넣는 방식으로 "입력창에 미리 채워주기"를 구현한다.
 */
export default function ChatInput({ placeholder, inputId, channelId, onSend, disabled }) {
  const { getDraft, setDraft, clearDraft, showToast } = useApp();
  const { t, languages, locale } = useI18n();
  const [listening, setListening] = useState(false);
  const text = getDraft(channelId);

  async function handleVoice() {
    if (!STT_READY) { showToast(t('chat.voiceSoon')); return; }
    if (listening || disabled) return;
    setListening(true);
    try {
      const tag = languages.find(l => l.code === locale)?.tag;
      const heard = (await recognizeSpeech({ lang: tag })).trim();
      if (heard) setDraft(channelId, text ? `${text} ${heard}` : heard);
    } catch (err) {
      console.warn('[stt] 음성 인식 실패', err);
    } finally {
      setListening(false);
    }
  }

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    clearDraft(channelId);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-input-bar">
      <input
        id={inputId}
        className="c-input"
        placeholder={placeholder}
        value={text}
        onChange={e => setDraft(channelId, e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        className={`mic-btn${listening ? ' listening' : ''}`}
        onClick={handleVoice}
        disabled={disabled}
        aria-label={t('chat.voiceInput')}
        title={t('chat.voiceInput')}
      >
        <MicIcon />
      </button>
      <button className="send-btn" onClick={handleSend} disabled={disabled}>
        <SendIcon />
      </button>
    </div>
  );
}
