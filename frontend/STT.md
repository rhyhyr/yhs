# STT integration

`src/hooks/useSpeechRecognition.js` provides browser-based speech recognition without UI or API keys. Existing ChatInput is unchanged.

## Button connection example

```jsx
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';

function VoiceInputExample({ onSend }) {
  const stt = useSpeechRecognition({ lang: 'ko-KR' });
  const active = stt.isListening;
  return (
    <>
      <button
        type="button"
        disabled={!stt.isSupported || stt.status === 'stopping'}
        onClick={() => active ? stt.stop() : stt.start()}
        aria-pressed={active}
      >
        {active ? 'Stop microphone' : 'Start microphone'}
      </button>
      <p aria-live="polite">{stt.transcript} {stt.interimTranscript}</p>
      {stt.error && <p role="alert">{stt.error.code}</p>}
      <button type="button" onClick={stt.cancel}>Cancel</button>
      <button
        type="button"
        disabled={!stt.transcript || !['idle', 'error'].includes(stt.status)}
        onClick={() => { onSend(stt.transcript); stt.cancel(); }}
      >Send confirmed text</button>
    </>
  );
}
```

For ChatInput, use this hook inside that component. Render the final transcript in a reviewable draft before sending. Do not call onSend for interim results. The example is documentation only; the button designer can supply their own UI.

## Contract

- `start()`: call from a user click. Clears the previous session; returns whether the start request was accepted, not whether microphone permission was granted. Duplicate calls during a session are ignored.
- `stop()`: stops listening and allows pending final results to arrive. Wait until status leaves `stopping` before starting or sending.
- `cancel()`: discards the transcript and aborts recognition. Unmount also aborts recognition.
- `transcript`: all final results in the current session; replace the displayed recognized text with this value, do not append the whole value repeatedly.
- `interimTranscript`: provisional text; it can change or disappear.
- `status`: idle / starting / listening / stopping / error.
- `error`: null or `{ code, message? }`. Translate codes for the UI: unsupported, insecure-context, not-allowed, service-not-allowed, audio-capture, no-speech, network, language-not-supported, aborted, start-failed, etc.
- `lang`: defaults to ko-KR. Use en-US or zh-CN as appropriate. Language changes take effect on the next start; changing UI language does not change an active session.
- `continuous`: defaults to false (one utterance). Even with true, the browser can end the session. No automatic restart.

## Runtime requirements and verification

Use localhost for local development and HTTPS for deployment. SpeechRecognition support and language availability vary by browser and device. Test on the actual target browsers; API presence alone does not guarantee that the recognition service works. Unsupported browsers should retain normal text input.

No .env changes or dependencies are needed. This is not a self-hosted transcription engine: some browsers send microphone audio to the browser vendor's recognition service and need network access. If consistent cross-browser behavior or controlled audio processing is required, use a backend STT service instead. Never put provider secrets in VITE_* variables.

Manual checks before shipping:

1. Allow microphone access, speak Korean, and confirm interim text becomes final text.
2. Stop during speech and confirm the last final result is preserved.
3. Cancel and leave the screen; confirm capture stops and late results are ignored.
4. Deny permission, disconnect the network, and test an unsupported browser; show the error and retain keyboard input.
5. Repeatedly click start/stop, start a fresh session, and confirm text is not duplicated.

Reference: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition