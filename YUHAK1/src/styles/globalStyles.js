export const globalStyles = `
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-tap-highlight-color: transparent;
  }

  :root {
    --c-accent: #2155CD;
    --c-accent-l: #E8EEFB;
    --c-accent-m: #8AAAF0;
    --c-red: #D13B3B;
    --c-red-l: #FAEAEA;
    --c-green: #1A8C5B;
    --c-green-l: #E4F5ED;
    --c-amber: #B5650D;
    --c-amber-l: #FDF0DC;
    --c-purple: #5B45C2;
    --c-purple-l: #EEEBFB;
    --c-bg: #F5F4F0;
    --c-surface: #FFFFFF;
    --c-border: #E2E0DA;
    --c-border-s: #C8C5BC;
    --c-t1: #1A1916;
    --c-t2: #6B6860;
    --c-t3: #A8A59E;
    --w: 393px;
    --h: 852px;
    --safe-top: 59px;
    --safe-bot: 34px;
    --radius-phone: 47px;
    --nav-h: 56px;
    --topbar-h: 52px;
  }

  html, body {
    width: 100%;
    min-height: 100vh;
    background: #1A1A1A;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Noto Sans KR', system-ui, sans-serif;
    overflow: auto;
    padding: 60px 24px;
  }

  #root {
    display: contents;
  }

  /* ── 아이폰 15 물리 바디 ── */
  .phone-wrapper {
    position: relative;
    background: #1C1C1E;
    border-radius: 54px;
    padding: 14px 10px;
    box-shadow:
      0 0 0 1px #48484A,
      0 0 0 2px #1C1C1E,
      0 0 0 3px #3A3A3C,
      0 60px 120px rgba(0,0,0,.85),
      inset 0 1px 0 rgba(255,255,255,.08);
    flex-shrink: 0;
  }

  /* 왼쪽 — 무음 스위치 + 볼륨 업/다운 */
  .phone-wrapper::before {
    content: '';
    position: absolute;
    left: -4px;
    top: 108px;
    width: 4px;
    height: 32px;
    background: #2C2C2E;
    border-radius: 2px 0 0 2px;
    box-shadow:
      0 50px 0 #2C2C2E,
      0 98px 0 4px #2C2C2E,
      0 98px 0 4px #2C2C2E;
  }

  /* 오른쪽 — 전원 버튼 */
  .phone-wrapper::after {
    content: '';
    position: absolute;
    right: -4px;
    top: 168px;
    width: 4px;
    height: 72px;
    background: #2C2C2E;
    border-radius: 0 2px 2px 0;
  }

  .iphone {
    position: relative;
    width: var(--w);
    height: var(--h);
    background: var(--c-surface);
    border-radius: var(--radius-phone);
    box-shadow:
      inset 0 0 0 1px rgba(255,255,255,.06);
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }

  .dynamic-island {
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 34px;
    background: #000;
    border-radius: 20px;
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .di-camera {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: #1A1A1A;
    border: 2px solid #2A2A2A;
  }

  .di-sensor {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #1A2B3A;
  }

  .status-bar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: var(--safe-top);
    padding: 0 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding-bottom: 10px;
    z-index: 100;
    background: #fff;
    font-size: 15px;
    font-weight: 600;
    color: var(--c-t1);
    letter-spacing: -.3px;
  }

  .sb-right {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }

  .sb-signal {
    display: flex;
    gap: 2px;
    align-items: flex-end;
  }

  .sb-bar {
    width: 3px;
    border-radius: 1px;
    background: var(--c-t1);
  }

  .home-indicator {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 134px;
    height: 5px;
    background: var(--c-t1);
    border-radius: 3px;
    opacity: .18;
    z-index: 100;
  }

  .screens {
    position: absolute;
    top: var(--safe-top);
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;
  }

  .screen {
    position: absolute;
    inset: 0;
    background: var(--c-surface);
    display: flex;
    flex-direction: column;
    opacity: 0;
    pointer-events: none;
    transform: translateX(24px);
    transition: opacity .22s ease, transform .22s ease;
  }

  .screen.active {
    opacity: 1;
    pointer-events: all;
    transform: translateX(0);
  }

  .screen.exit-left {
    opacity: 0;
    transform: translateX(-24px);
    pointer-events: none;
  }

  .topbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px 10px;
    padding-top: 6px;
    background: var(--c-surface);
    border-bottom: 1px solid var(--c-border);
    flex-shrink: 0;
    min-height: var(--topbar-h);
  }

  .tb-back {
    font-size: 13px;
    color: var(--c-accent);
    cursor: pointer;
    padding: 4px;
    margin-left: -4px;
    display: flex;
    align-items: center;
    gap: 3px;
    font-weight: 500;
  }

  .tb-back svg { width: 8px; height: 14px; }

  .tb-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--c-t1);
    letter-spacing: -.3px;
    flex: 1;
  }

  .tb-sub {
    font-size: 12px;
    color: var(--c-t2);
    margin-top: 1px;
  }

  .tb-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 10px;
  }

  .scroll-area {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .scroll-area::-webkit-scrollbar { display: none; }

  .bottom-nav {
    height: calc(var(--nav-h) + var(--safe-bot));
    padding-bottom: var(--safe-bot);
    border-top: 1px solid var(--c-border);
    display: flex;
    background: rgba(255,255,255,.92);
    backdrop-filter: blur(20px);
    flex-shrink: 0;
  }

  .bnav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    font-size: 10px;
    color: var(--c-t3);
    cursor: pointer;
    transition: color .15s;
    padding-top: 4px;
  }

  .bnav-item.active { color: var(--c-accent); }

  .bnav-icon {
    width: 26px;
    height: 26px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    transition: background .15s;
  }

  .bnav-item.active .bnav-icon { background: var(--c-accent-l); }

  .sec-lbl {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .8px;
    text-transform: uppercase;
    color: var(--c-t3);
    padding: 12px 16px 4px;
  }

  .ch-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--c-border);
    cursor: pointer;
    transition: background .1s;
    -webkit-tap-highlight-color: rgba(0,0,0,.04);
  }

  .ch-item:active { background: #F5F4F0; }

  .ch-item--urgent {
    border-left: 3px solid var(--c-red);
    background: #FFF9F9;
  }

  .ch-item--urgent:active { background: var(--c-red-l); }

  .sec-lbl--warn { color: var(--c-red); }

  .sec-lbl--blue { color: var(--c-accent); }

  .ch-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }

  .ch-body { flex: 1; min-width: 0; }

  .ch-name {
    font-size: 15px;
    font-weight: 500;
    color: var(--c-t1);
  }

  .ch-preview {
    font-size: 13px;
    color: var(--c-t2);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ch-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
  }

  .ch-time { font-size: 12px; color: var(--c-t3); }

  .badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
  }

  .info-chip {
    display: flex;
    align-items: center;
    gap: 7px;
    background: var(--c-bg);
    border: 1px solid var(--c-border);
    border-radius: 10px;
    padding: 9px 12px;
    margin: 10px 16px 0;
    font-size: 12px;
    color: var(--c-t2);
  }

  .info-chip strong { color: var(--c-t1); font-weight: 500; }

  .info-chip.urgent {
    background: var(--c-red-l);
    border-color: #F5B8B8;
  }

  .info-chip.urgent strong { color: var(--c-red); }

  .qa-scroll {
    display: flex;
    gap: 8px;
    padding: 10px 16px 8px;
    overflow-x: auto;
    scrollbar-width: none;
    flex-shrink: 0;
  }

  .qa-scroll::-webkit-scrollbar { display: none; }

  .qa-btn {
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 500;
    padding: 8px 14px;
    border: 1.5px solid var(--c-border-s);
    border-radius: 20px;
    background: var(--c-surface);
    color: var(--c-t1);
    cursor: pointer;
    white-space: nowrap;
    font-family: inherit;
    transition: all .15s;
  }

  .qa-btn:active {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
  }

  /* 채팅에서 생성된 체크리스트 퀵액션 버튼 */
  .qa-btn-checklist {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
    font-weight: 600;
  }

  .qa-btn-checklist:active {
    background: #D4E2FA;
  }

  .chat-area {
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .msg-ai { display: flex; gap: 8px; align-items: flex-end; }

  .ai-av {
    width: 30px;
    height: 30px;
    border-radius: 10px;
    background: var(--c-accent-l);
    border: 1px solid var(--c-accent-m);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: var(--c-accent);
    flex-shrink: 0;
    letter-spacing: -.5px;
  }

  .bubble-ai {
    background: #F0EFEB;
    border: 1px solid var(--c-border);
    border-radius: 18px 18px 18px 4px;
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.55;
    color: var(--c-t1);
    max-width: 252px;
  }

  .msg-user { display: flex; justify-content: flex-end; }

  .bubble-user {
    background: var(--c-accent);
    color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.55;
    max-width: 252px;
  }

  .tags-row {
    display: flex;
    gap: 5px;
    padding-left: 38px;
    flex-wrap: wrap;
    margin-top: -4px;
  }

  .tag {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 10px;
    font-weight: 500;
  }

  /* ── 구조화 메시지 렌더링 (ChatMessage) ─────────────────────── */

  .msg-spacer { height: 6px; }

  .msg-line { margin: 1px 0; }

  .msg-section {
    font-weight: 700;
    font-size: 13px;
    color: var(--c-t1);
    margin: 8px 0 3px;
  }

  .msg-step {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin: 3px 0;
  }

  .msg-step-num {
    min-width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--c-accent);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .msg-bullet {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin: 2px 0;
    color: var(--c-t2);
    font-size: 13px;
  }

  .msg-bullet-dot {
    color: var(--c-accent);
    font-size: 14px;
    line-height: 1.55;
    flex-shrink: 0;
  }

  /* ── 체크리스트 제안 CTA 카드 ──────────────────────────────────── */

  .checklist-cta-card {
    margin: 8px 0 4px;
    background: var(--c-surface);
    border: 1.5px solid var(--c-accent-m);
    border-radius: 14px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .checklist-cta-icon {
    font-size: 22px;
    line-height: 1;
  }

  .checklist-cta-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .checklist-cta-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--c-t1);
  }

  .checklist-cta-desc {
    font-size: 12px;
    color: var(--c-t2);
    line-height: 1.5;
  }

  .checklist-cta-actions {
    display: flex;
    gap: 8px;
  }

  .checklist-cta-yes {
    flex: 1;
    background: var(--c-accent);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 9px 0;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    font-family: inherit;
  }

  .checklist-cta-no {
    flex: 1;
    background: var(--c-bg);
    color: var(--c-t2);
    border: 1px solid var(--c-border);
    border-radius: 10px;
    padding: 9px 0;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
  }

  .msg-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin-top: 8px;
  }

  .msg-tag {
    background: var(--c-accent-l);
    color: var(--c-accent);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
  }

  .chat-input-bar {
    padding: 10px 14px 12px;
    border-top: 1px solid var(--c-border);
    display: flex;
    gap: 10px;
    align-items: center;
    flex-shrink: 0;
    background: var(--c-surface);
  }

  .c-input {
    flex: 1;
    background: var(--c-bg);
    border: 1.5px solid var(--c-border);
    border-radius: 22px;
    padding: 10px 16px;
    font-size: 15px;
    color: var(--c-t3);
    font-family: inherit;
    outline: none;
  }

  .c-input:focus {
    border-color: var(--c-accent-m);
    color: var(--c-t1);
    background: var(--c-surface);
  }

  .send-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--c-accent);
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform .1s, opacity .1s;
  }

  .send-btn:active { transform: scale(.92); opacity: .85; }

  .slim-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    border-bottom: 1px solid var(--c-border);
    flex-shrink: 0;
    background: var(--c-surface);
    min-height: var(--topbar-h);
  }

  .slim-ch-icon {
    width: 30px;
    height: 30px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }

  .slim-ch-name {
    font-size: 16px;
    font-weight: 600;
    color: var(--c-t1);
  }

  .slim-rag {
    font-size: 10px;
    font-weight: 600;
    padding: 3px 7px;
    border-radius: 8px;
    background: var(--c-green-l);
    color: var(--c-green);
  }

  .slim-d87 {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    color: var(--c-red);
    background: var(--c-red-l);
    border: 1px solid #F5B8B8;
    border-radius: 8px;
    padding: 4px 9px;
    cursor: pointer;
  }

  .info-panel {
    padding: 8px 16px;
    border-bottom: 1px solid var(--c-border);
    background: #FAFAF8;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    transition: all .2s;
  }

  .i-chip {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    color: var(--c-t2);
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: 8px;
    padding: 6px 10px;
  }

  .i-chip strong { color: var(--c-t1); font-weight: 500; }

  .i-chip.green {
    background: var(--c-green-l);
    border-color: #A7F3D0;
    color: var(--c-green);
  }

  .progress-wrap { padding: 12px 16px 4px; }

  .progress-bg {
    height: 5px;
    background: var(--c-border);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--c-green);
    border-radius: 3px;
    transition: width .4s ease;
  }

  .prog-label {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--c-t3);
    margin-top: 5px;
  }

  .step-card {
    margin: 8px 14px;
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    overflow: hidden;
  }

  .step-card-hdr {
    background: var(--c-accent-l);
    padding: 9px 14px;
    font-size: 12px;
    font-weight: 600;
    color: var(--c-accent);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .step-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 11px 14px;
    border-top: 1px solid var(--c-border);
    cursor: pointer;
    transition: background .1s;
  }

  .step-row:active { background: var(--c-bg); }

  .step-cb {
    width: 22px;
    height: 22px;
    border-radius: 7px;
    border: 2px solid var(--c-border-s);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
    transition: all .15s;
    cursor: pointer;
  }

  .step-cb.checked {
    background: var(--c-green);
    border-color: var(--c-green);
    color: #fff;
    font-size: 13px;
  }

  .step-cb.current {
    border-color: var(--c-accent);
    background: var(--c-accent-l);
  }

  .step-label { flex: 1; }

  .step-text {
    font-size: 13px;
    line-height: 1.4;
    color: var(--c-t1);
  }

  .step-text.done {
    text-decoration: line-through;
    color: var(--c-t3);
  }

  .step-sub {
    font-size: 11px;
    color: var(--c-t2);
    margin-top: 3px;
  }

  .step-sub.done { color: var(--c-t3); }

  .save-note {
    margin: 6px 14px;
    padding: 10px 13px;
    background: var(--c-green-l);
    border: 1px solid #A7F3D0;
    border-radius: 11px;
    font-size: 12px;
    color: var(--c-green);
  }

  .cta-card {
    margin: 4px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border: 1.5px solid var(--c-accent-m);
    border-radius: 12px;
    background: var(--c-accent-l);
    cursor: pointer;
    transition: opacity .1s;
  }

  .cta-card:active { opacity: .8; }

  .cta-icon {
    width: 30px;
    height: 30px;
    border-radius: 9px;
    background: var(--c-surface);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    flex-shrink: 0;
  }

  .cta-body { flex: 1; }

  .cta-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--c-accent);
  }

  .cta-sub {
    font-size: 11px;
    color: var(--c-accent-m);
    margin-top: 2px;
  }

  .cta-arrow { font-size: 18px; color: var(--c-accent); }

  .cta-card.neutral {
    background: var(--c-surface);
    border-color: var(--c-border-s);
  }

  .cta-card.neutral .cta-title { color: var(--c-t1); }
  .cta-card.neutral .cta-sub { color: var(--c-t2); }
  .cta-card.neutral .cta-arrow { color: var(--c-t2); }

  .ans-wrap {
    margin: 4px 14px;
    border: 1.5px solid var(--c-border);
    border-radius: 12px;
    overflow: hidden;
  }

  .ans-domain {
    padding: 7px 13px;
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .ans-dot { width: 8px; height: 8px; border-radius: 50%; }

  .ans-body {
    padding: 10px 13px;
    font-size: 13px;
    line-height: 1.55;
    color: var(--c-t1);
    border-top: 1px solid var(--c-border);
  }

  .ans-tags {
    padding: 7px 13px 10px;
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }

  .k-card {
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    overflow: hidden;
    margin: 0 14px;
    cursor: pointer;
    transition: box-shadow .15s;
  }

  .k-card:active { box-shadow: 0 2px 12px rgba(33,85,205,.12); }

  .k-card-body { padding: 13px 14px; }

  .k-q {
    font-size: 14px;
    font-weight: 600;
    color: var(--c-t1);
    margin-bottom: 5px;
    line-height: 1.35;
  }

  .k-preview {
    font-size: 12px;
    color: var(--c-t2);
    line-height: 1.5;
  }

  .k-card-foot {
    padding: 8px 14px;
    border-top: 1px solid var(--c-border);
    background: #FAFAF8;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .kd-q-box {
    margin: 12px 14px;
    padding: 12px 14px;
    background: var(--c-accent-l);
    border: 1.5px solid var(--c-accent-m);
    border-radius: 12px;
  }

  .kd-q-label {
    font-size: 10px;
    font-weight: 600;
    color: var(--c-accent-m);
    letter-spacing: .5px;
    margin-bottom: 5px;
  }

  .kd-q-text {
    font-size: 15px;
    font-weight: 600;
    color: var(--c-accent);
    line-height: 1.35;
  }

  .kd-block-text {
    padding: 0 14px 12px;
    font-size: 14px;
    line-height: 1.7;
    color: var(--c-t1);
  }

  .kd-list-block {
    margin: 0 14px 12px;
    padding: 12px 14px;
    background: var(--c-bg);
    border: 1.5px solid var(--c-border);
    border-radius: 12px;
  }

  .kd-list-title {
    font-size: 12px;
    font-weight: 600;
    color: var(--c-t2);
    margin-bottom: 10px;
    letter-spacing: .3px;
  }

  .kd-list-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    margin-bottom: 8px;
  }

  .kd-list-item:last-child { margin-bottom: 0; }

  .kd-num {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--c-accent);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .kd-source {
    margin: 0 14px 12px;
    padding: 8px 12px;
    background: var(--c-bg);
    border: 1px solid var(--c-border);
    border-radius: 10px;
    font-size: 11px;
    color: var(--c-t3);
  }

  .kd-section-lbl {
    padding: 8px 14px 6px;
    font-size: 12px;
    font-weight: 600;
    color: var(--c-t2);
    letter-spacing: .3px;
  }

  .related-q {
    margin: 0 14px 8px;
    padding: 12px 14px;
    border: 1.5px solid var(--c-border);
    border-radius: 11px;
    font-size: 13px;
    color: var(--c-t1);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--c-surface);
    transition: background .1s;
  }

  .related-q:active { background: var(--c-bg); }

  .ob-hero { padding: 40px 20px 20px; text-align: left; }
  .ob-mark { font-size: 52px; margin-bottom: 16px; display: block; }

  .ob-h {
    font-size: 24px;
    font-weight: 700;
    color: var(--c-t1);
    margin-bottom: 8px;
    letter-spacing: -.5px;
  }

  .ob-p { font-size: 14px; color: var(--c-t2); line-height: 1.65; }

  .social-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 0 16px 10px;
    padding: 15px;
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    background: var(--c-surface);
    color: var(--c-t1);
    font-family: inherit;
    transition: all .15s;
    width: calc(100% - 32px);
  }

  .social-btn:active { background: var(--c-bg); }

  .ob-steps {
    display: flex;
    gap: 6px;
    justify-content: center;
    padding: 0 0 16px;
  }

  .ob-step-dot {
    width: 28px;
    height: 4px;
    border-radius: 2px;
    background: var(--c-border);
  }

  .ob-step-dot.done { background: var(--c-accent); }
  .ob-step-dot.active { background: var(--c-accent); }

  .form-sec {
    padding: 4px 16px 2px;
    font-size: 13px;
    font-weight: 600;
    color: var(--c-t1);
  }

  .form-note { padding: 0 16px 10px; font-size: 12px; color: var(--c-t2); }

  .form-group {
    padding: 0 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .f-label { font-size: 12px; font-weight: 500; color: var(--c-t2); }

  .f-input {
    background: var(--c-bg);
    border: 1.5px solid var(--c-border);
    border-radius: 11px;
    padding: 12px 14px;
    font-size: 15px;
    color: var(--c-t1);
    font-family: inherit;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .f-input.filled {
    background: var(--c-surface);
    border-color: var(--c-border-s);
  }

  .chip-row { display: flex; gap: 7px; flex-wrap: wrap; }

  .sel-chip {
    font-size: 13px;
    padding: 8px 16px;
    border: 1.5px solid var(--c-border);
    border-radius: 22px;
    cursor: pointer;
    background: var(--c-surface);
    color: var(--c-t2);
    font-family: inherit;
    transition: all .15s;
  }

  .sel-chip.on {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
    font-weight: 500;
  }

  .lang-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    padding: 0 16px 16px;
  }

  .lang-card {
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    padding: 14px;
    cursor: pointer;
    text-align: center;
    transition: all .15s;
    background: var(--c-surface);
  }

  .lang-card.on {
    border-color: var(--c-accent-m);
    background: var(--c-accent-l);
  }

  .lang-flag { font-size: 26px; margin-bottom: 5px; }
  .lang-name { font-size: 13px; font-weight: 600; color: var(--c-t1); }
  .lang-sub { font-size: 11px; color: var(--c-t3); margin-top: 2px; }

  .ob-note {
    margin: 4px 16px 20px;
    padding: 10px 13px;
    background: #FEF3C7;
    border: 1px solid #FCD34D;
    border-radius: 11px;
    font-size: 12px;
    color: #92400E;
  }

  .cta-primary {
    margin: 4px 16px 20px;
    padding: 16px;
    background: var(--c-accent);
    color: #fff;
    border: none;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    text-align: center;
    width: calc(100% - 32px);
    transition: opacity .1s, transform .1s;
  }

  .cta-primary:active { opacity: .85; transform: scale(.98); }

  .footnote {
    text-align: left;
    font-size: 12px;
    color: var(--c-t3);
    padding: 0 16px 20px;
  }

  .ch-tabs {
    display: flex;
    border-bottom: 1px solid var(--c-border);
    flex-shrink: 0;
    background: var(--c-surface);
  }

  .ch-tab {
    flex: 1;
    text-align: center;
    padding: 11px 0;
    font-size: 13px;
    color: var(--c-t2);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all .15s;
    font-weight: 400;
  }

  .ch-tab.active {
    color: var(--c-accent);
    border-bottom-color: var(--c-accent);
    font-weight: 600;
  }

  .search-bar {
    margin: 10px 14px;
    display: flex;
    align-items: center;
    gap: 9px;
    background: var(--c-bg);
    border: 1.5px solid var(--c-border);
    border-radius: 12px;
    padding: 10px 13px;
  }

  .search-bar span { font-size: 14px; color: var(--c-t3); }

  .filter-row {
    display: flex;
    gap: 7px;
    padding: 0 14px 10px;
    overflow-x: auto;
    scrollbar-width: none;
    flex-shrink: 0;
  }

  .filter-row::-webkit-scrollbar { display: none; }

  .filter-chip {
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 500;
    padding: 6px 13px;
    border: 1.5px solid var(--c-border);
    border-radius: 16px;
    cursor: pointer;
    background: var(--c-surface);
    color: var(--c-t2);
    font-family: inherit;
    transition: all .15s;
    white-space: nowrap;
  }

  .filter-chip.active {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
  }

  .result-card {
    margin: 0 14px 10px;
    border: 1.5px solid var(--c-border);
    border-radius: 13px;
    overflow: hidden;
    cursor: pointer;
    transition: box-shadow .15s;
  }

  .result-card:active { box-shadow: 0 2px 10px rgba(0,0,0,.08); }

  .result-inner { display: flex; gap: 10px; padding: 11px 13px; }

  .result-ch-icon {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
  }

  .result-body { flex: 1; min-width: 0; }

  .result-q {
    font-size: 13px;
    font-weight: 500;
    color: var(--c-t1);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .result-p {
    font-size: 12px;
    color: var(--c-t2);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .result-foot {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
  }

  .r-time { font-size: 11px; color: var(--c-t3); }

  .profile-hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px 16px;
    border-bottom: 1px solid var(--c-border);
  }

  .p-av {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: var(--c-accent-l);
    border: 2.5px solid var(--c-accent-m);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 700;
    color: var(--c-accent);
    margin-bottom: 12px;
  }

  .p-name { font-size: 18px; font-weight: 700; color: var(--c-t1); letter-spacing: -.4px; }
  .p-school { font-size: 13px; color: var(--c-t2); margin-top: 3px; }

  .p-badges {
    display: flex;
    gap: 7px;
    margin-top: 10px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .p-badge {
    font-size: 12px;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 12px;
  }

  .visa-card {
    margin: 12px 14px;
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    overflow: hidden;
  }

  .vc-hdr {
    background: var(--c-purple-l);
    padding: 9px 13px;
    font-size: 12px;
    font-weight: 600;
    color: var(--c-purple);
  }

  .vc-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 13px;
    border-top: 1px solid var(--c-border);
  }

  .vc-label { font-size: 12px; color: var(--c-t2); }
  .vc-val { font-size: 13px; font-weight: 500; color: var(--c-t1); }

  .vc-btn {
    margin: 8px 13px 10px;
    padding: 9px;
    background: var(--c-accent-l);
    border: 1.5px solid var(--c-accent-m);
    border-radius: 10px;
    text-align: center;
    font-size: 13px;
    font-weight: 500;
    color: var(--c-accent);
    cursor: pointer;
  }

  .setting-sec {
    padding: 14px 16px 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .8px;
    text-transform: uppercase;
    color: var(--c-t3);
  }

  .setting-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 13px 16px;
    border-bottom: 1px solid var(--c-border);
    cursor: pointer;
    transition: background .1s;
  }

  .setting-row:active { background: var(--c-bg); }

  .s-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    flex-shrink: 0;
  }

  .s-name { font-size: 15px; font-weight: 500; color: var(--c-t1); }
  .s-val { font-size: 12px; color: var(--c-t2); margin-top: 2px; }
  .s-body { flex: 1; }

  .toggle-track {
    width: 50px;
    height: 28px;
    border-radius: 14px;
    position: relative;
    cursor: pointer;
    flex-shrink: 0;
    transition: background .2s;
  }

  .toggle-track.on { background: var(--c-accent); }
  .toggle-track.off { background: #D1D5DB; }

  .toggle-knob {
    position: absolute;
    top: 3px;
    width: 22px;
    height: 22px;
    background: #fff;
    border-radius: 50%;
    transition: left .2s;
    box-shadow: 0 1px 4px rgba(0,0,0,.2);
  }

  .toggle-track.on .toggle-knob { left: 25px; }
  .toggle-track.off .toggle-knob { left: 3px; }

  .logout-btn {
    margin: 14px 16px;
    padding: 13px;
    border: 1.5px solid var(--c-red-l);
    border-radius: 13px;
    text-align: center;
    font-size: 15px;
    font-weight: 500;
    color: var(--c-red);
    cursor: pointer;
    transition: background .1s;
  }

  .logout-btn:active { background: var(--c-red-l); }

  .notif-btn { position: relative; cursor: pointer; }

  .notif-bubble {
    position: absolute;
    top: -4px;
    right: -4px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--c-red);
    color: #fff;
    font-size: 9px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--c-surface);
  }

  .toast {
    position: absolute;
    bottom: calc(var(--nav-h) + var(--safe-bot) + 16px);
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: rgba(26,25,22,.9);
    color: #fff;
    padding: 10px 18px;
    border-radius: 22px;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    opacity: 0;
    transition: all .25s ease;
    pointer-events: none;
    z-index: 500;
    backdrop-filter: blur(12px);
  }

  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  /* ── SourceModal ── */
  .source-modal-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, .45);
    z-index: 500;
    display: flex;
    align-items: flex-end;
  }

  .source-modal-sheet {
    width: 100%;
    background: var(--c-surface);
    border-radius: 20px 20px 0 0;
    padding: 12px 16px 28px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    animation: slideUp .22s ease;
  }

  @keyframes slideUp {
    from { transform: translateY(100%); }
    to   { transform: translateY(0); }
  }

  .source-modal-handle {
    width: 36px;
    height: 4px;
    border-radius: 2px;
    background: var(--c-border-s);
    align-self: center;
    margin-bottom: 4px;
  }

  .source-modal-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--c-t1);
  }

  .source-modal-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .source-modal-item {
    padding: 10px 12px;
    background: var(--c-bg);
    border-radius: 10px;
  }

  .source-modal-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--c-t1);
  }

  .source-modal-detail {
    font-size: 12px;
    color: var(--c-t2);
    margin-top: 3px;
  }

  .source-modal-close {
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 12px;
    background: var(--c-bg);
    font-size: 14px;
    font-weight: 500;
    color: var(--c-t1);
    cursor: pointer;
  }

  .kd-source { cursor: pointer; }
  .kd-source:active { opacity: .7; }

  /* ── 채널 카드 ── */
  .channel-card {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .channel-text {
    flex: 1;
    text-align: left;
  }

  .channel-title {
    font-weight: 600;
  }

  .channel-desc {
    font-size: 14px;
    color: #666;
  }

  /* ── 홈 — 빈 채널 상태 UI ── */
  .empty-channel-card {
    margin: 6px 14px 8px;
    padding: 20px 16px 18px;
    background: var(--c-bg);
    border: 1.5px dashed var(--c-border-s);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .empty-channel-cta {
    width: 100%;
    padding: 11px;
    background: var(--c-accent);
    color: #fff;
    border: none;
    border-radius: 11px;
    font-size: 13px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: opacity .15s;
  }

  .empty-channel-cta:active { opacity: .85; }

  /* ── 홈 — ghost(예시) 채널 ── */
  .ghost-ch-item {
    opacity: 0.42;
    pointer-events: auto;
    filter: grayscale(20%);
  }

  .ghost-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 8px;
    background: var(--c-border);
    color: var(--c-t3);
    border: 1px dashed var(--c-border-s);
  }

  /* ── 메인 채팅 — 웰컴 카드 ── */
  .main-welcome-card {
    margin: 16px 14px 8px;
    padding: 22px 18px 20px;
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F4F0 100%);
    border: 1.5px solid var(--c-accent-m);
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 8px;
  }

  .mwc-emoji {
    font-size: 32px;
    line-height: 1;
    margin-bottom: 2px;
  }

  .mwc-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--c-t1);
    letter-spacing: -.3px;
  }

  .mwc-desc {
    font-size: 13px;
    color: var(--c-t2);
    line-height: 1.65;
  }

  .mwc-btn {
    margin-top: 6px;
    width: 100%;
    padding: 13px;
    background: var(--c-accent);
    color: #fff;
    border: none;
    border-radius: 13px;
    font-size: 14px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: opacity .15s;
  }

  .mwc-btn:active { opacity: .85; }

  /* ── 메인 채팅 — 카테고리 단축칩 ── */
  .main-shortcut-chip {
    flex-shrink: 0;
    position: relative;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 16px;
    border: 1.5px solid var(--c-border-s);
    border-radius: 20px;
    background: var(--c-surface);
    color: var(--c-t1);
    cursor: pointer;
    white-space: nowrap;
    font-family: inherit;
    transition: all .15s;
  }

  .main-shortcut-chip:active {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
  }

  .main-shortcut-chip.created {
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
    color: var(--c-accent);
    font-weight: 600;
  }

  .chip-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--c-accent);
    margin-left: 5px;
    vertical-align: middle;
    position: relative;
    top: -1px;
  }

  .main-shortcut-chip.suggested {
    background: var(--c-accent-l);
    border-color: var(--c-accent);
    color: var(--c-accent);
    font-weight: 600;
    animation: chip-pulse 1.6s ease-in-out infinite;
  }

  @keyframes chip-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(33, 85, 205, 0.25); }
    50%       { box-shadow: 0 0 0 6px rgba(33, 85, 205, 0); }
  }

  .suggestion-card {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 4px 0 8px;
    padding: 13px 14px;
    background: var(--c-accent-l);
    border: 1.5px solid var(--c-accent-m);
    border-radius: 14px;
    cursor: pointer;
    transition: opacity .15s;
  }
  .suggestion-card:active { opacity: .78; }
  .suggestion-card-text {
    flex: 1;
    font-size: 13px;
    color: var(--c-accent);
    font-weight: 500;
    line-height: 1.45;
  }
  .suggestion-card-arrow {
    font-size: 20px;
    color: var(--c-accent-m);
  }

  /* ── 메인 채팅 — 채널 생성 모달 ── */
  .channel-modal-sheet {
    width: 100%;
    background: var(--c-surface);
    border-radius: 24px 24px 0 0;
    padding: 14px 16px 32px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: slideUp .22s ease;
  }

  .channel-modal-btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 13px;
    font-size: 15px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: opacity .15s;
  }

  .channel-modal-btn:active { opacity: .82; }

  .channel-modal-btn.primary {
    background: var(--c-accent);
    color: #fff;
  }

  .channel-modal-btn.secondary {
    background: var(--c-bg);
    color: var(--c-t2);
    font-weight: 500;
  }

  /* ── 이미지 공통 (향후 이미지 추가 대비) ── */
  img {
    max-width: 100%;
    height: auto;
    display: block;
  }

  /* ═══════════════════════════════════════════════════════════
     반응형 레이아웃
     데스크톱  ≥ 1024px : 현재 상태 유지 (아이폰 목업 + 어두운 배경)
     태블릿   ≤  768px : 상하 여백 축소, 폰 프레임 반경 축소
     모바일   ≤  480px : 폰 프레임 제거, 전체화면 앱 모드
  ═══════════════════════════════════════════════════════════ */

  /* 태블릿 (≤ 768px) */
  @media (max-width: 768px) {
    html, body {
      padding: 24px 16px;
    }

    .phone-wrapper {
      border-radius: 44px;
    }

    /* 말풍선 너비를 뷰포트 기반으로 유연화 */
    .bubble-ai,
    .bubble-user {
      max-width: min(252px, calc(100vw - 80px));
    }
  }

  /* 모바일 (≤ 480px) — 폰 프레임 제거, 전체화면 앱 모드 */
  @media (max-width: 480px) {
    html, body {
      padding: 0;
      background: var(--c-surface);
      display: block;
      min-height: 100vh;
      min-height: 100dvh;
      overflow: hidden;
    }

    /* 폰 외형 껍데기 제거 */
    .phone-wrapper {
      border-radius: 0;
      padding: 0;
      background: transparent;
      box-shadow: none;
      width: 100%;
      display: block;
    }

    /* 가짜 측면 버튼 숨김 */
    .phone-wrapper::before,
    .phone-wrapper::after {
      display: none;
    }

    /* 아이폰 화면 → 전체화면 */
    .iphone {
      width: 100%;
      max-width: 100%;
      height: 100vh;
      height: 100dvh;
      border-radius: 0;
      box-shadow: none;
    }

    /* 말풍선 너비 뷰포트 기반으로 전환 */
    .bubble-ai,
    .bubble-user {
      max-width: calc(100vw - 80px);
    }

    /* 토스트 메시지가 화면 밖으로 나가지 않도록 */
    .toast {
      max-width: calc(100% - 32px);
      white-space: normal;
      text-align: center;
    }

    /* 카드류 좌우 넘침 방지 */
    .step-card,
    .k-card,
    .ans-wrap,
    .visa-card,
    .cta-card,
    .result-card,
    .kd-list-block,
    .related-q {
      max-width: 100%;
    }

    /* 채팅 입력창이 좁은 화면에서도 한 줄로 유지 */
    .chat-input-bar {
      padding: 8px 12px 10px;
    }

    /* 칩 행 — 좁은 화면에서 가로 스크롤 허용 (줄바꿈 없이) */
    .qa-scroll,
    .filter-row {
      padding-bottom: 8px;
    }

    /* 온보딩 히어로 패딩 축소 */
    .ob-hero {
      padding: 28px 16px 16px;
    }
  }

  /* ── 캘린더 페이지 ─────────────────────────────────────── */

  .cal-nav-group {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .cal-today-btn {
    font-size: 12px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 8px;
    border: 1.5px solid var(--c-border);
    background: var(--c-surface);
    color: var(--c-accent);
    cursor: pointer;
    font-family: inherit;
    transition: background .1s;
    line-height: 1;
  }

  .cal-today-btn:active { background: var(--c-bg); }

  .cal-nav-btn {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    border: 1.5px solid var(--c-border);
    background: var(--c-surface);
    color: var(--c-t2);
    cursor: pointer;
    font-size: 17px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: inherit;
    transition: background .1s;
    line-height: 1;
  }

  .cal-nav-btn:active { background: var(--c-bg); }

  .cal-month-label {
    padding: 14px 16px 8px;
    font-size: 22px;
    font-weight: 700;
    color: var(--c-t1);
    letter-spacing: -.5px;
  }

  .cal-weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    padding: 0 10px 4px;
  }

  .cal-weekday {
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--c-t3);
    padding: 4px 0 6px;
  }

  .cal-weekday.sun { color: #D13B3B99; }
  .cal-weekday.sat { color: #2155CD88; }

  .cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    padding: 0 10px 8px;
    gap: 1px 0;
  }

  .cal-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 3px 2px 5px;
    cursor: pointer;
    border-radius: 10px;
    min-height: 48px;
    transition: background .1s;
  }

  .cal-cell:active { background: var(--c-bg); }

  .cal-cell.other-month { cursor: default; opacity: .38; }
  .cal-cell.other-month:active { background: transparent; }

  .cal-date {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 500;
    color: var(--c-t1);
    transition: all .1s;
  }

  .cal-cell.today .cal-date {
    background: var(--c-accent);
    color: #fff;
    font-weight: 700;
  }

  .cal-cell.selected:not(.today) .cal-date {
    background: var(--c-t1);
    color: #fff;
    font-weight: 700;
  }

  .cal-cell.today.selected .cal-date {
    background: var(--c-accent);
    color: #fff;
    font-weight: 700;
    box-shadow: 0 0 0 3px var(--c-accent-m);
  }

  .cal-dots {
    display: flex;
    gap: 3px;
    margin-top: 4px;
    align-items: center;
    height: 6px;
  }

  .cal-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .cal-divider {
    height: 1px;
    background: var(--c-border);
    margin: 4px 16px 0;
  }

  .cal-events-section {
    padding: 14px 14px 28px;
  }

  .cal-events-hdr {
    display: flex;
    align-items: baseline;
    gap: 7px;
    margin-bottom: 12px;
  }

  .cal-events-date {
    font-size: 16px;
    font-weight: 700;
    color: var(--c-t1);
    letter-spacing: -.3px;
  }

  .cal-events-dow {
    font-size: 13px;
    color: var(--c-t3);
    font-weight: 500;
  }

  .cal-events-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .cal-event-card {
    display: flex;
    border: 1.5px solid var(--c-border);
    border-radius: 14px;
    overflow: hidden;
    background: var(--c-surface);
    cursor: pointer;
    transition: background .1s;
  }

  .cal-event-card:active { background: var(--c-bg); }

  .cal-event-bar {
    width: 4px;
    flex-shrink: 0;
  }

  .cal-event-body {
    flex: 1;
    padding: 12px 13px;
  }

  .cal-event-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--c-t1);
    line-height: 1.3;
  }

  .cal-event-desc {
    font-size: 12px;
    color: var(--c-t2);
    margin-top: 4px;
    line-height: 1.45;
  }

  .cal-event-meta {
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .cal-event-type {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 8px;
  }

  .cal-event-completed {
    font-size: 11px;
    font-weight: 600;
    color: var(--c-green);
    background: var(--c-green-l);
    padding: 3px 9px;
    border-radius: 8px;
  }

  .cal-event-source {
    font-size: 11px;
    font-weight: 500;
    color: var(--c-t3);
    background: var(--c-bg);
    border: 1px solid var(--c-border);
    padding: 2px 8px;
    border-radius: 8px;
  }

  .cal-event-card.completed {
    opacity: .75;
  }

  .cal-event-title.done {
    text-decoration: line-through;
    color: var(--c-t3);
  }

  .cal-empty {
    padding: 32px 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    border: 1.5px dashed var(--c-border);
    border-radius: 14px;
    background: var(--c-bg);
  }

  .cal-empty-icon {
    font-size: 28px;
    margin-bottom: 4px;
    opacity: .6;
  }

  .cal-empty-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--c-t2);
  }

  .cal-empty-sub {
    font-size: 12px;
    color: var(--c-t3);
    text-align: center;
    line-height: 1.55;
    max-width: 220px;
  }

  .cal-event-source.chat {
    color: var(--c-accent);
    background: var(--c-accent-l);
    border-color: var(--c-accent-m);
  }

  /* ── 채팅 체크리스트 확인 카드 ────────────────────────────── */

  .cl-confirm {
    margin: 4px 0 8px;
    padding: 14px;
    border-radius: 16px;
    border: 1.5px solid var(--c-accent-m);
    background: var(--c-accent-l);
  }

  .cl-confirm-top {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 8px;
  }

  .cl-confirm-icon { font-size: 18px; }

  .cl-confirm-chip {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 8px;
  }

  .cl-confirm-body {
    font-size: 13px;
    color: var(--c-t1);
    line-height: 1.6;
    margin-bottom: 12px;
  }

  .cl-confirm-actions {
    display: flex;
    gap: 8px;
  }

  .cl-confirm-yes {
    flex: 1;
    padding: 9px;
    border-radius: 10px;
    background: var(--c-accent);
    color: #fff;
    font-weight: 700;
    font-size: 14px;
    border: none;
    cursor: pointer;
    font-family: inherit;
    transition: opacity .1s;
  }

  .cl-confirm-yes:active { opacity: .85; }

  .cl-confirm-no {
    padding: 9px 18px;
    border-radius: 10px;
    background: transparent;
    color: var(--c-t3);
    font-size: 14px;
    font-weight: 500;
    border: 1.5px solid var(--c-border);
    cursor: pointer;
    font-family: inherit;
    transition: background .1s;
  }

  .cl-confirm-no:active { background: var(--c-bg); }

  /* 연동 완료 후 리다이렉트 카드 — 초록 계열 */
  .cl-redirect-confirm {
    border-color: #A8D5C0;
    background: var(--c-green-l);
  }

  .cl-redirect-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--c-green);
    background: #fff;
    padding: 3px 9px;
    border-radius: 8px;
    border: 1px solid #A8D5C0;
  }

  /* 캘린더 연동 카드 — 파란 accent 계열 */
  .cl-cal-confirm {
    border-color: var(--c-accent-m);
    background: var(--c-accent-l);
  }

  .cl-cal-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--c-accent);
    background: #fff;
    padding: 3px 9px;
    border-radius: 8px;
    border: 1px solid var(--c-accent-m);
  }

  /* ── 인라인 체크리스트 카드 ────────────────────────────────── */

  .cl-created-card {
    margin: 4px 0 8px;
    border-radius: 16px;
    border: 1.5px solid var(--c-border);
    background: var(--c-surface);
    overflow: hidden;
  }

  .cl-created-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 11px 14px;
    background: var(--c-bg);
    border-bottom: 1px solid var(--c-border);
  }

  .cl-created-icon { font-size: 16px; }

  .cl-created-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--c-t1);
  }

  .cl-created-list { padding: 2px 0; }

  .cl-created-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 14px;
    border-bottom: 1px solid var(--c-border);
  }

  .cl-created-item:last-child { border-bottom: none; }

  .cl-created-cb {
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 2px solid var(--c-border-s);
    flex-shrink: 0;
  }

  .cl-created-text {
    flex: 1;
    font-size: 13px;
    color: var(--c-t1);
    line-height: 1.35;
  }

  .cl-created-date {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 6px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .cl-created-footer {
    padding: 8px 14px;
    font-size: 11px;
    color: var(--c-t3);
    background: var(--c-bg);
    border-top: 1px solid var(--c-border);
  }

  /* ── 체크리스트 네비게이션 버튼 카드 ─────────────────────── */

  .cl-nav-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 14px;
    margin: 4px 0 8px;
    border-radius: 14px;
    border: 1.5px solid;
    cursor: pointer;
    transition: filter .1s;
  }

  .cl-nav-card:active { filter: brightness(.96); }

  .cl-nav-icon { font-size: 22px; flex-shrink: 0; }

  .cl-nav-body { flex: 1; min-width: 0; }

  .cl-nav-title {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -.2px;
  }

  .cl-nav-sub {
    font-size: 12px;
    color: var(--c-t2);
    margin-top: 2px;
  }

  .cl-nav-arrow {
    font-size: 22px;
    font-weight: 700;
    flex-shrink: 0;
  }

  /* ── 체크리스트 선택 모달 시트 ────────────────────────────── */

  .cl-sheet {
    width: 100%;
    background: var(--c-surface);
    border-radius: 22px 22px 0 0;
    padding: 8px 0 0;
    display: flex;
    flex-direction: column;
    max-height: 88%;
  }

  .cl-sheet-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 6px 16px 12px;
    gap: 8px;
  }

  .cl-sheet-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--c-t1);
    letter-spacing: -.3px;
    margin-bottom: 3px;
  }

  .cl-sheet-subtitle {
    font-size: 12px;
    color: var(--c-t2);
  }

  .cl-sheet-all-btn {
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 600;
    color: var(--c-accent);
    background: var(--c-accent-l);
    border: none;
    border-radius: 8px;
    padding: 5px 10px;
    cursor: pointer;
    font-family: inherit;
    margin-top: 2px;
    white-space: nowrap;
  }

  .cl-sheet-list {
    flex: 1;
    overflow-y: auto;
    scrollbar-width: none;
    border-top: 1px solid var(--c-border);
    padding: 4px 0;
  }

  .cl-sheet-list::-webkit-scrollbar { display: none; }

  .cl-sheet-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 16px;
    cursor: pointer;
    transition: background .1s;
    border-bottom: 1px solid var(--c-border);
  }

  .cl-sheet-item:last-child { border-bottom: none; }
  .cl-sheet-item:active { background: var(--c-bg); }
  .cl-sheet-item.checked { background: #FAFAF8; }

  .cl-sheet-cb {
    width: 22px;
    height: 22px;
    border-radius: 7px;
    border: 2px solid var(--c-border-s);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 13px;
    font-weight: 700;
    color: transparent;
    transition: all .15s;
  }

  .cl-sheet-cb.checked {
    background: var(--c-accent);
    border-color: var(--c-accent);
    color: #fff;
  }

  .cl-sheet-item-content {
    flex: 1;
    min-width: 0;
  }

  .cl-sheet-item-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--c-t1);
    line-height: 1.35;
  }

  .cl-sheet-item.checked .cl-sheet-item-title { color: var(--c-t1); }

  .cl-sheet-item-sub {
    font-size: 11px;
    color: var(--c-t3);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cl-sheet-item-date {
    flex-shrink: 0;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 7px;
  }

  .cl-sheet-footer {
    display: flex;
    gap: 8px;
    padding: 10px 16px 20px;
    border-top: 1px solid var(--c-border);
  }

  .cl-sheet-cancel {
    padding: 12px 18px;
    border-radius: 12px;
    background: var(--c-bg);
    color: var(--c-t2);
    font-size: 14px;
    font-weight: 500;
    border: 1.5px solid var(--c-border);
    cursor: pointer;
    font-family: inherit;
  }

  .cl-sheet-confirm {
    flex: 1;
    padding: 12px;
    border-radius: 12px;
    background: var(--c-accent);
    color: #fff;
    font-size: 14px;
    font-weight: 700;
    border: none;
    cursor: pointer;
    font-family: inherit;
    transition: opacity .1s;
  }

  .cl-sheet-confirm:disabled {
    background: var(--c-border);
    color: var(--c-t3);
    cursor: default;
  }

  .cl-sheet-confirm:not(:disabled):active { opacity: .85; }
`;

