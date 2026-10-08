import { createContext, useState, useRef, useEffect, useMemo } from 'react';
import { INITIAL_STEPS, ARC_RENEW_STEPS, SCHOOL_REGISTER_STEPS } from '../api/mockData';
import { getVisaSteps, updateStepStatus } from '../api/steps';
import { persistUserProfile } from '../api/userProfile';
import { loadUserProfile } from '../utils/storage';
import { mergeEvents } from '../api/calendar';
import { buildAnswerHistory } from '../utils/answerHistory';
import { requestGoogleAccessToken } from '../utils/googleAuth';
import { useI18n } from '../i18n';

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
  const { t } = useI18n();

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
  const [activeFilter, setActiveFilter] = useState('all');
  const [activeFilter2, setActiveFilter2] = useState('extend');

  // ── 채널 메인 필터 ──
  const [channelFilter, setChannelFilter] = useState('all');

  // ── 채팅 체크리스트 → 캘린더 연동 이벤트 맵 ──
  // 형식: { 'YYYY-MM-DD': [CalendarEvent, ...] }
  const [chatCalendarItems, setChatCalendarItems] = useState({});

  function addChatChecklistToCalendar(eventMap) {
    setChatCalendarItems(prev => mergeEvents(prev, eventMap));
  }

  // ── 구글 캘린더 연동 (로그인 없이, 백엔드 없이 — OAuth 토큰 플로우) ──
  // 접근 토큰은 메모리에만 둔다. 새로고침하면 날아가고(의도된 동작),
  // 1시간 정도 지나면 구글 쪽에서 만료시켜서 다시 연결해야 한다.
  const [googleAccessToken, setGoogleAccessToken] = useState(null);
  const [googleConnecting, setGoogleConnecting] = useState(false);

  async function connectGoogleCalendar() {
    setGoogleConnecting(true);
    try {
      const token = await requestGoogleAccessToken();
      setGoogleAccessToken(token);
      showToast(t('google.connected'));
    } catch (err) {
      if (err.message === 'NO_CLIENT_ID' || err.message === 'GIS_NOT_LOADED') {
        showToast(t('google.notConfigured'));
      } else {
        // 사용자가 팝업을 닫은 경우(access_denied 등) 포함 — 조용히 취소 처리
        showToast(t('google.connectCancelled'));
      }
    } finally {
      setGoogleConnecting(false);
    }
  }

  function disconnectGoogleCalendar() {
    setGoogleAccessToken(null);
  }

  // API 호출 중 토큰 만료(401)를 만나면 화면 쪽에서 이걸 불러서 연결 상태를 초기화한다
  function invalidateGoogleToken() {
    setGoogleAccessToken(null);
    showToast(t('google.tokenExpired'));
  }

  // ── 사용자가 생성한 채널 목록 (ChatScreen → HomeScreen 공유) ──
  const [createdChannels, setCreatedChannels] = useState([]);

  function addCreatedChannel(channel) {
    setCreatedChannels(prev =>
      prev.find(c => c.id === channel.id) ? prev : [...prev, { pinned: false, ...channel }]
    );
  }

  // ── 채널 상단 고정 ──
  function toggleChannelPin(id) {
    setCreatedChannels(prev =>
      prev.map(c => (c.id === id ? { ...c, pinned: !c.pinned } : c))
    );
  }

  // 고정된 채널이 위로 오도록 정렬한 목록 — 화면에 내 채널을 보여주는 곳은
  // 다 이 정렬된 배열을 써야 하므로, 원본 대신 이 값을 createdChannels로 내보낸다.
  // (Array.sort는 안정 정렬이라 고정 여부가 같으면 기존 순서가 유지된다)
  const sortedCreatedChannels = useMemo(
    () => [...createdChannels].sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0)),
    [createdChannels]
  );

  // ── 채널별 채팅 상태 ──
  const [chatState, setChatState] = useState({});

  // ── 채널별 "작성 중인" 입력창 내용 ──
  // ChatInput이 더 이상 자체 state를 안 갖고 이걸 직접 읽고 쓴다.
  // 그래서 다른 화면 갔다 와도(언마운트돼도) 내용이 안 사라지고,
  // 빠른 질문 버튼도 같은 방식으로 "입력창 채우기"를 구현한다.
  const [drafts, setDrafts] = useState({});

  function getDraft(channelId) {
    return drafts[channelId] ?? '';
  }

  function setDraft(channelId, text) {
    setDrafts(prev => ({ ...prev, [channelId]: text }));
  }

  function clearDraft(channelId) {
    setDrafts(prev => {
      if (!(channelId in prev)) return prev;
      const next = { ...prev };
      delete next[channelId];
      return next;
    });
  }

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

  // "기록" 탭에서 보여줄 실제 질문/답변 목록 — 새 저장소 없이 chatState에서 파생시킨다
  const answerHistory = useMemo(() => buildAnswerHistory(chatState), [chatState]);

  // ── 함수 ──
  function navigate(id, params = {}) {
    if (id === 'notif-placeholder') { showToast(t('toast.notifSoon')); return; }
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
        showToast(t('toast.allStepsDone'));
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
        showToast(t('toast.schoolDone'));
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
        showToast(t('toast.arcDone'));
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
      addMessage, getMessages, answerHistory,
      // 채팅 입력창 임시저장(draft)
      getDraft, setDraft, clearDraft,
      // 채팅 체크리스트 → 캘린더
      chatCalendarItems, addChatChecklistToCalendar,
      // 구글 캘린더 연동
      googleAccessToken, googleConnecting, connectGoogleCalendar, disconnectGoogleCalendar, invalidateGoogleToken,
      // 생성된 채널 (고정된 채널이 위로 오도록 정렬된 상태로 내보냄)
      createdChannels: sortedCreatedChannels, addCreatedChannel, toggleChannelPin,
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
