import { useEffect } from 'react';
import { AppProvider } from './store/AppContext';
import { useApp } from './hooks/useApp';
import { globalStyles } from './styles/globalStyles';

import HomeScreen from './pages/HomeScreen';
import VisaScreen from './pages/VisaScreen';
import StepGuideScreen from './pages/StepGuideScreen';
import ChatScreen from './pages/ChatScreen';
import CalendarScreen from './pages/CalendarScreen';
import ChannelMainScreen from './pages/ChannelMainScreen';
import KnowledgeScreen from './pages/KnowledgeScreen';
import OnboardingScreen from './pages/OnboardingScreen';
import SearchScreen from './pages/SearchScreen';
import ProfileScreen from './pages/ProfileScreen';

/* ── 화면 전환 클래스를 결정하는 헬퍼 ── */
function useScreenClass(current, prev) {
  return (id) => {
    if (id === current) return 'screen active';
    if (id === prev) return 'screen exit-left';
    return 'screen';
  };
}

/* ── 앱 본체 (Provider 내부에서 실행) ── */
function AppShell() {
  const { current, prev, toastMsg, toastVisible } = useApp();
  const sc = useScreenClass(current, prev);

  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.textContent = globalStyles;
    document.head.appendChild(styleEl);
    return () => document.head.removeChild(styleEl);
  }, []);

  return (
    <div className="iphone">
      {/* Dynamic Island */}
      <div className="dynamic-island">
        <div className="di-sensor" />
        <div className="di-camera" />
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <span>9:41</span>
        <div className="sb-right">
          <div className="sb-signal">
            <div className="sb-bar" style={{ height: '4px' }} />
            <div className="sb-bar" style={{ height: '6px' }} />
            <div className="sb-bar" style={{ height: '9px' }} />
            <div className="sb-bar" style={{ height: '12px' }} />
          </div>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="none">
            <rect x="0" y="3" width="13" height="9" rx="2" stroke="#1A1916" strokeWidth="1.5" />
            <rect x="1.5" y="4.5" width="8" height="6" rx="1" fill="#1A1916" />
            <path d="M14 5v4a2 2 0 000-4z" fill="#1A1916" opacity=".4" />
          </svg>
          <span style={{ fontSize: '13px' }}>95%</span>
        </div>
      </div>

      {/* Home Indicator */}
      <div className="home-indicator" />

      {/* ── 화면 목록 ── */}
      <div className="screens">
        <div className={sc('s-home')}        id="s-home">        <HomeScreen /></div>
        <div className={sc('s-visa')}        id="s-visa">        <VisaScreen /></div>
        <div className={sc('s-step')}        id="s-step">        <StepGuideScreen /></div>
        <div className={sc('s-main')}        id="s-main">        <ChatScreen /></div>
        <div className={sc('s-calendar')}    id="s-calendar">    <CalendarScreen /></div>
        <div className={sc('s-channel-main')}id="s-channel-main"><ChannelMainScreen /></div>
        <div className={sc('s-knowledge')}   id="s-knowledge">   <KnowledgeScreen /></div>
        <div className={sc('s-onboarding')}  id="s-onboarding">  <OnboardingScreen /></div>
        <div className={sc('s-search')}      id="s-search">      <SearchScreen /></div>
        <div className={sc('s-profile')}     id="s-profile">     <ProfileScreen /></div>
      </div>

      {/* Toast */}
      <div className={`toast${toastVisible ? ' show' : ''}`}>{toastMsg}</div>
    </div>
  );
}

export default function UniGuideApp() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
