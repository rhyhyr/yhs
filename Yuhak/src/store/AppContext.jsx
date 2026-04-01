import { createContext, useState, useRef } from 'react';
import { INITIAL_STEPS } from '../api/mockData';

// 안정적인 빈 배열 참조 — useEffect 의존성 배열에서 무한루프 방지
const EMPTY_MESSAGES = [];

export const AppContext = createContext(null);

export function AppProvider({ children }) {
  // ── 네비게이션 ──
  const [current, setCurrent] = useState('s-home');
  const [prev, setPrev] = useState(null);
  const [historyStack, setHistoryStack] = useState(['s-home']);

  // ── 토스트 ──
  const [toastMsg, setToastMsg] = useState('');
  const [toastVisible, setToastVisible] = useState(false);
  const toastTimer = useRef(null);

  // ── 비자 단계 체크리스트 ──
  const [steps, setSteps] = useState(INITIAL_STEPS);

  // ── 알림 토글 ──
  const [toggles, setToggles] = useState({ visa: true, house: true, insurance: false });

  // ── 온보딩: 언어 선택 ──
  const [langs, setLangs] = useState({ ko: true, zh: true, en: false, vi: false });

  // ── 온보딩: 비자 유형 선택 ──
  const [visaChip, setVisaChip] = useState('D-2 학생');

  // ── 비자 채널: 정보 패널 열림 여부 ──
  const [infoOpen, setInfoOpen] = useState(true);

  // ── 검색 필터 ──
  const [activeFilter, setActiveFilter] = useState('전체');
  const [activeFilter2, setActiveFilter2] = useState('#연장');

  // ── 채널 메인 필터 ──
  const [channelFilter, setChannelFilter] = useState('전체');

  // ── 채널별 채팅 상태 ──
  const [chatState, setChatState] = useState({});

  // ── 파생 값 (단계 진행률) ──
  const total = steps.length;
  const checkedCount = steps.filter(s => s.checked).length;
  const pct = Math.round(checkedCount / total * 100);
  const grp1Checked = steps.slice(0, 4).filter(s => s.checked).length;
  const grp2Checked = steps.slice(4).filter(s => s.checked).length;

  // ── 채팅 함수 ──
  // EMPTY_MESSAGES는 모듈 상수로 안정적인 참조 유지 (useEffect 무한루프 방지)
  function addMessage(channelId, msg) {
    setChatState(prev => ({
      ...prev,
      [channelId]: [...(prev[channelId] ?? []), msg],
    }));
  }

  function getMessages(channelId) {
    return chatState[channelId] ?? EMPTY_MESSAGES;
  }

  // ── 함수 ──
  function navigate(id) {
    if (id === 'notif-placeholder') { showToast('알림 화면으로 이동합니다'); return; }
    if (id === current) return;
    setPrev(current);
    setCurrent(id);
    setHistoryStack(h => [...h, id]);
  }

  function back() {
    if (historyStack.length <= 1) return;
    const newStack = [...historyStack];
    newStack.pop();
    const nextScreen = newStack[newStack.length - 1];
    setPrev(current);
    setCurrent(nextScreen);
    setHistoryStack(newStack);
  }

  function showToast(msg) {
    setToastMsg(msg);
    setToastVisible(true);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToastVisible(false), 2200);
  }

  function toggleStep(id) {
    setSteps(prevSteps => {
      const updated = prevSteps.map(s => {
        if (s.id === id) {
          const nowChecked = !s.checked;
          return { ...s, checked: nowChecked, current: !nowChecked };
        }
        return s;
      });
      if (updated.filter(s => s.checked).length === total) {
        showToast('🎉 모든 단계를 완료했습니다!');
      }
      return updated;
    });
  }

  return (
    <AppContext.Provider value={{
      // 네비게이션
      current, prev, navigate, back,
      // 토스트
      toastMsg, toastVisible, showToast,
      // 단계
      steps, toggleStep, checkedCount, total, pct, grp1Checked, grp2Checked,
      // 프로필/설정
      toggles, setToggles,
      langs, setLangs,
      visaChip, setVisaChip,
      // 채팅 상태
      addMessage, getMessages,
      // 채널
      infoOpen, setInfoOpen,
      activeFilter, setActiveFilter,
      activeFilter2, setActiveFilter2,
      channelFilter, setChannelFilter,
    }}>
      {children}
    </AppContext.Provider>
  );
}
