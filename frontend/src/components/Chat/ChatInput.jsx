import { useEffect, useRef } from 'react';
import { useApp } from '../../hooks/useApp';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useI18n } from '../../i18n';
import { SendIcon, MicIcon } from '../Common/icons';

/**
 * ChatInput
 *
 * props:
 *   channelId — 어느 채널의 입력창인지 (draft를 채널별로 구분해서 저장하기 위함)
 *   onSend(text) — 전송 시 입력 텍스트를 인자로 전달
 *
 * 🎙️ 버튼: useSpeechRecognition 훅으로 인식된 문장을 입력창에 채운다 (전송은 사용자가 직접).
 * 인식 중 버튼을 다시 누르면 현재 음성을 확정하고 인식을 중지한다.
 *
 * 입력 중인 텍스트는 이 컴포넌트가 들고 있지 않고 AppContext의 draft로 관리한다.
 * 그래서 다른 화면으로 이동했다가 돌아와도(=이 컴포넌트가 언마운트/재마운트돼도)
 * 작성 중이던 내용이 그대로 남아있고, 채널별 빠른 질문 버튼도 같은 draft를
 * 채워 넣는 방식으로 "입력창에 미리 채워주기"를 구현한다.
 */
export default function ChatInput({ placeholder, inputId, channelId, onSend, disabled }) {
  const { getDraft, setDraft, clearDraft, showToast } = useApp();
  const { t, languages, locale } = useI18n();
  const text = getDraft(channelId);
  const lang = languages.find(language => language.code === locale)?.tag ?? 'ko-KR';
  const {
    isSupported,
    status,
    transcript,
    error,
    start,
    stop,
  } = useSpeechRecognition({ lang });
  const textRef = useRef(text);
  const appliedTranscriptRef = useRef('');
  const handledErrorRef = useRef(null);
  const voiceActive = status === 'starting' || status === 'listening' || status === 'stopping';

  useEffect(() => {
    textRef.current = text;
  }, [text]);

  useEffect(() => {
    if (!transcript || transcript === appliedTranscriptRef.current) return;

    const previousTranscript = appliedTranscriptRef.current;
    const currentText = textRef.current;
    const baseText = previousTranscript && currentText.endsWith(previousTranscript)
      ? currentText.slice(0, -previousTranscript.length).trimEnd()
      : currentText.trimEnd();
    const nextText = baseText ? `${baseText} ${transcript}` : transcript;

    appliedTranscriptRef.current = transcript;
    textRef.current = nextText;
    setDraft(channelId, nextText);
  }, [channelId, setDraft, transcript]);

  useEffect(() => {
    if (!error || handledErrorRef.current === error) return;
    handledErrorRef.current = error;
    console.warn('[stt] voice recognition failed', error);

    if (error.code === 'not-allowed' || error.code === 'service-not-allowed') {
      showToast(t('chat.voicePermissionDenied'));
    } else if (error.code === 'no-speech') {
      showToast(t('chat.voiceNoSpeech'));
    } else if (error.code === 'unsupported' || error.code === 'insecure-context') {
      showToast(t('chat.voiceUnsupported'));
    } else if (error.code !== 'aborted') {
      showToast(t('chat.voiceError'));
    }
  }, [error, showToast, t]);

  function handleVoice() {
    if (disabled || status === 'stopping') return;
    if (!isSupported) {
      showToast(t('chat.voiceUnsupported'));
      return;
    }
    if (status === 'starting' || status === 'listening') {
      stop();
      return;
    }

    appliedTranscriptRef.current = '';
    start();
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
        type="button"
        className={`mic-btn${voiceActive ? ' listening' : ''}`}
        onClick={handleVoice}
        disabled={disabled || status === 'stopping'}
        aria-label={voiceActive ? t('chat.voiceStop') : t('chat.voiceInput')}
        aria-pressed={voiceActive}
        title={voiceActive ? t('chat.voiceStop') : t('chat.voiceInput')}
      >
        <MicIcon />
      </button>
      <button className="send-btn" onClick={handleSend} disabled={disabled}>
        <SendIcon />
      </button>
    </div>
  );
}
