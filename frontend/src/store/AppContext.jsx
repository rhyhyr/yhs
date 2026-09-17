import { createContext, useState, useRef, useEffect } from 'react';
import { INITIAL_STEPS, ARC_RENEW_STEPS, SCHOOL_REGISTER_STEPS } from '../api/mockData';
import { getVisaSteps, updateStepStatus } from '../api/steps';
import { persistUserProfile } from '../api/userProfile';
import { loadUserProfile } from '../utils/storage';
import { mergeEvents } from '../api/calendar';

const DEFAULT_PROFILE = {
  name: '',
  nationality: '',
  school: '',
  department: '',
  grade: '',
  visaType: '',
  languages: [],
};

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

  useEffect(() => {
    getVisaSteps().then(setSteps).catch(() => {});
  }, []);

  // ── 외국인등록증 재발급 체크리스트 ──
  const [arcSteps, setArcSteps] = useState(ARC_RENEW_STEPS);

  // ── 학교 수강신청·등록 체크리스트 ──
  const [schoolSteps, setSchoolSteps] = useState(SCHOOL_REGISTER_STEPS);

  // ── 알림 토글 ──
  const [toggles, setToggles] = useState({ visa: true, house: true, insurance: false });

  // ── 유저 프로필 ──
  const [userProfile, setUserProfile] = useState(() => loadUserProfile() ?? DEFAULT_PROFILE);

  function saveProfile(profile) {
    persistUserProfile(profile);
    setUserProfile(profile);
  }

  function updateUserProfile(partial) {
    const updated = { ...userProfile, ...partial };
    persistUserProfile(updated);
    setUserProfile(updated);
  }

  // ── 비자 채널: 정보 패널 열림 여부 ──
  const [infoOpen, setInfoOpen] = useState(true);

  // ── 검색 필터 ──
  const [activeFilter, setActiveFilter] = useState('전체');
  const [activeFilter2, setActiveFilter2] = useState('#연장');

  // ── 채널 메인 필터 ──
  const [channelFilter, setChannelFilter] = useState('전체');

  // ── 채팅 체크리스트 → 캘린더 연동 이벤트 맵 ──
  // 형식: { 'YYYY-MM-DD': [CalendarEvent, ...] }
  const [chatCalendarItems, setChatCalendarItems] = useState({});

  function addChatChecklistToCalendar(eventMap) {
    setChatCalendarItems(prev => mergeEvents(prev, eventMap));
  }

  // ── 사용자가 생성한 채널 목록 (ChatScreen → HomeScreen 공유) ──
  const [createdChannels, setCreatedChannels] = useState([]);

  function addCreatedChannel(channel) {
    setCreatedChannels(prev =>
      prev.find(c => c.id === channel.id) ? prev : [...prev, channel]
    );
  }

  // ── 채널별 채팅 상태 ──
  const [chatState, setChatState] = useState({});

  // ── 네비게이션 파라미터 (채널 ID 등 화면 전환 시 전달할 데이터) ──
  const [navParams, setNavParams] = useState({});

  // ── 파생 값 (비자 연장 진행률) ──
  const total = steps.length;
  const checkedCount = steps.filter(s => s.checked).length;
  const pct = Math.round(checkedCount / total * 100);
  const grp1Checked = steps.slice(0, 4).filter(s => s.checked).length;
  const grp2Checked = steps.slice(4).filter(s => s.checked).length;

  // ── 파생 값 (외국인등록증 재발급 진행률) ──
  const arcTotal = arcSteps.length;
  const arcCheckedCount = arcSteps.filter(s => s.checked).length;
  const arcPct = Math.round(arcCheckedCount / arcTotal * 100);
  const arcGrp1Checked = arcSteps.slice(0, 4).filter(s => s.checked).length;
  const arcGrp2Checked = arcSteps.slice(4).filter(s => s.checked).length;

  // ── 파생 값 (학교 수강신청·등록 진행률) ──
  const schoolTotal = schoolSteps.length;
  const schoolCheckedCount = schoolSteps.filter(s => s.checked).length;
  const schoolPct = Math.round(schoolCheckedCount / schoolTotal * 100);
  const schoolGrp1Checked = schoolSteps.slice(0, 4).filter(s => s.checked).length;
  const schoolGrp2Checked = schoolSteps.slice(4).filter(s => s.checked).length;

  // ── 채팅 함수 ──
  // EMPTY_MESSAGES는 모듈 상수로 안정적인 참조 유지 (useEffect 무한루프 방지)
  function addMessage(channelId, msg) {
    const fullMsg = {
      sources: [],
      tags: [],
      createdAt: Date.now(),
      ...msg,
    };
    setChatState(prev => ({
      ...prev,
      [channelId]: [...(prev[channelId] ?? []), fullMsg],
    }));
  }

  function getMessages(channelId) {
    return chatState[channelId] ?? EMPTY_MESSAGES;
  }

  // ── 함수 ──
  function navigate(id, params = {}) {
    if (id === 'notif-placeholder') { showToast('알림 화면으로 이동합니다'); return; }
    if (id === current) return;
    setPrev(current);
    setCurrent(id);
    setNavParams(params);
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
          updateStepStatus(id, nowChecked).catch(() => {});
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

  function toggleSchoolStep(id) {
    setSchoolSteps(prevSteps => {
      const updated = prevSteps.map(s => {
        if (s.id === id) {
          const nowChecked = !s.checked;
          return { ...s, checked: nowChecked, current: !nowChecked };
        }
        return s;
      });
      if (updated.filter(s => s.checked).length === schoolTotal) {
        showToast('🎉 수강신청 준비가 모두 완료됐어요!');
      }
      return updated;
    });
  }

  function toggleArcStep(id) {
    setArcSteps(prevSteps => {
      const updated = prevSteps.map(s => {
        if (s.id === id) {
          const nowChecked = !s.checked;
          return { ...s, checked: nowChecked, current: !nowChecked };
        }
        return s;
      });
      if (updated.filter(s => s.checked).length === arcTotal) {
        showToast('🎉 재발급 준비가 모두 완료됐어요!');
      }
      return updated;
    });
  }

  return (
    <AppContext.Provider value={{
      // 네비게이션
      current, prev, navParams, navigate, back,
      // 토스트
      toastMsg, toastVisible, showToast,
      // 단계 (비자 연장)
      steps, toggleStep, checkedCount, total, pct, grp1Checked, grp2Checked,
      // 단계 (외국인등록증 재발급)
      arcSteps, toggleArcStep, arcCheckedCount, arcTotal, arcPct, arcGrp1Checked, arcGrp2Checked,
      // 단계 (학교 수강신청·등록)
      schoolSteps, toggleSchoolStep, schoolCheckedCount, schoolTotal, schoolPct, schoolGrp1Checked, schoolGrp2Checked,
      // 프로필/설정
      toggles, setToggles,
      // 유저 프로필
      userProfile, saveUserProfile: saveProfile, updateUserProfile,
      // 채팅 상태
      addMessage, getMessages,
      // 채팅 체크리스트 → 캘린더
      chatCalendarItems, addChatChecklistToCalendar,
      // 생성된 채널
      createdChannels, addCreatedChannel,
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
