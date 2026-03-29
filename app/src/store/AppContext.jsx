import { createContext, useState, useRef } from 'react';
import { INITIAL_STEPS } from '../api/mockData';

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

  // ── 파생 값 (단계 진행률) ──
  const total = steps.length;
  const checkedCount = steps.filter(s => s.checked).length;
  const pct = Math.round(checkedCount / total * 100);
  const grp1Checked = steps.slice(0, 4).filter(s => s.checked).length;
  const grp2Checked = steps.slice(4).filter(s => s.checked).length;

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
