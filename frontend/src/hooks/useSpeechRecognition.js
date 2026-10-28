import { useCallback, useEffect, useRef, useState } from 'react';

function getRecognition() {
  return typeof window === 'undefined'
    ? undefined
    : window.SpeechRecognition || window.webkitSpeechRecognition;
}

/** UI-independent STT. Call start() directly from a user click. */
export function useSpeechRecognition({ lang = 'ko-KR', continuous = false } = {}) {
  const recognitionRef = useRef(null);
  const [status, setStatus] = useState('idle');
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState(null);
  const isSupported = Boolean(getRecognition());

  const start = useCallback(() => {
    if (recognitionRef.current) return false;
    const Recognition = getRecognition();
    if (!Recognition || !window.isSecureContext) {
      setError({ code: !Recognition ? 'unsupported' : 'insecure-context' });
      setStatus('error');
      return false;
    }

    let recognition;
    try {
      recognition = new Recognition();
      recognition.lang = lang;
      recognition.continuous = continuous;
      recognition.interimResults = true;
      recognitionRef.current = recognition;
      setTranscript('');
      setInterimTranscript('');
      setError(null);
      setStatus('starting');

      recognition.onstart = () => {
        if (recognitionRef.current === recognition) setStatus('listening');
      };
      recognition.onresult = (event) => {
        if (recognitionRef.current !== recognition) return;
        const final = [];
        const interim = [];
        for (let i = 0; i < event.results.length; i += 1) {
          const result = event.results[i];
          (result.isFinal ? final : interim).push(result[0].transcript);
        }
        setTranscript(final.join(' ').trim());
        setInterimTranscript(interim.join(' ').trim());
      };
      recognition.onerror = (event) => {
        if (recognitionRef.current !== recognition) return;
        setError({ code: event.error || 'unknown' });
        setInterimTranscript('');
        setStatus('error');
      };
      recognition.onend = () => {
        if (recognitionRef.current !== recognition) return;
        recognitionRef.current = null;
        setInterimTranscript('');
        setStatus((current) => current === 'error' ? 'error' : 'idle');
      };
      recognition.start();
      return true;
    } catch (cause) {
      recognitionRef.current = null;
      if (recognition) {
        recognition.onstart = recognition.onresult = recognition.onerror = recognition.onend = null;
        recognition.abort();
      }
      setError({ code: 'start-failed', message: cause.message });
      setStatus('error');
      return false;
    }
  }, [lang, continuous]);

  // stop keeps pending final results; wait for onend before starting again.
  const stop = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    recognition.stop();
    setStatus((current) => current === 'error' ? current : 'stopping');
  }, []);

  // cancel discards this session and prevents late events from changing state.
  const cancel = useCallback(() => {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.onstart = recognition.onresult = recognition.onerror = recognition.onend = null;
      recognition.abort();
      recognitionRef.current = null;
    }
    setTranscript('');
    setInterimTranscript('');
    setError(null);
    setStatus('idle');
  }, []);

  useEffect(() => () => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    recognition.onstart = recognition.onresult = recognition.onerror = recognition.onend = null;
    recognition.abort();
    recognitionRef.current = null;
  }, []);

  return {
    isSupported, status, transcript, interimTranscript, error,
    isListening: status === 'starting' || status === 'listening',
    start, stop, cancel,
  };
}