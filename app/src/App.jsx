import { useState, useEffect, useRef, useCallback } from "react";

/* ══════════════════════════════════════════════════════
   UniGuide AI — React Prototype
   원본 HTML(iphone15.html) 과 완전히 동일하게 구현
══════════════════════════════════════════════════════ */

const globalStyles = `
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
  }

  .iphone {
    position: relative;
    width: var(--w);
    height: var(--h);
    background: var(--c-surface);
    border-radius: var(--radius-phone);
    box-shadow:
      0 0 0 11px #1C1C1E,
      0 0 0 13px #3A3A3C,
      0 0 0 14px #1C1C1E,
      0 40px 80px rgba(0,0,0,.7),
      inset 0 0 0 1px rgba(255,255,255,.08);
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
    background: var(--c-surface);
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
    bottom: 0;
    left: 0;
    right: 0;
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
    display: block;
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

  .search-bar svg { flex-shrink: 0; }
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

  /* ── Calendar cells ── */
  .cal-cell {
    min-height: 64px;
    border: 1px solid var(--c-border);
    border-radius: 14px;
    background: var(--c-surface);
    padding: 8px 4px 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: all .15s ease;
  }

  .cal-cell:active { transform: scale(.97); }

  .cal-cell.other-month {
    background: #FAFAF8;
    color: var(--c-t3);
  }

  .cal-cell.today {
    border-color: var(--c-accent-m);
    background: var(--c-accent-l);
  }

  .cal-cell.selected {
    border-color: var(--c-accent);
    box-shadow: 0 0 0 2px rgba(33,85,205,.08);
  }

  .cal-date {
    font-size: 13px;
    font-weight: 500;
    color: var(--c-t1);
  }

  .cal-cell.other-month .cal-date { color: var(--c-t3); }

  .cal-cell.today .cal-date {
    color: var(--c-accent);
    font-weight: 700;
  }

  .cal-dots {
    display: flex;
    gap: 3px;
    margin-top: 6px;
    flex-wrap: wrap;
    justify-content: center;
    min-height: 10px;
  }

  .cal-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }
`;

/* ── 캘린더 이벤트 데이터 (원본 JS와 동일) ── */
const calendarEvents = {
  '2026-08-10': [{ title: '비자 연장 서류 준비', color: '#5B45C2', type: '비자', desc: '만료 35일 전 — 서류 준비 권장' }],
  '2026-08-15': [{ title: 'D-2 비자 만료일', color: '#D13B3B', type: '비자', desc: '이 날 이전에 연장 완료 필수' }],
  '2026-08-20': [{ title: '건강보험료 납부', color: '#1A8C5B', type: '보험', desc: '8월분 납부 마감' }],
  '2026-08-25': [{ title: '수강신청 정정기간', color: '#2155CD', type: '학교', desc: '학교 포털에서 정정 가능' }],
};

function formatDateKey(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

/* ── SVG 아이콘 ── */
const BackIcon = () => (
  <svg viewBox="0 0 8 14" fill="none">
    <path d="M7 1L1 7l6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M2 8h12M9 3l5 5-5 5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="7" cy="7" r="5" stroke="var(--c-t3)" strokeWidth="1.5" />
    <path d="M11 11l3 3" stroke="var(--c-t3)" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

/* ── 하단 네비게이션 ── */
const BottomNav = ({ active, navigate }) => {
  const items = [
    { id: 's-home', icon: '⊞', label: '홈' },
    { id: 's-main', icon: '💬', label: '채팅' },
    { id: 's-calendar', icon: '📅', label: '캘린더' },
    { id: 's-search', icon: '🔍', label: '검색' },
    { id: 's-profile', icon: '👤', label: '내정보' },
  ];
  return (
    <div className="bottom-nav">
      {items.map(item => (
        <div
          key={item.id}
          className={`bnav-item${active === item.id ? ' active' : ''}`}
          onClick={() => navigate(item.id)}
        >
          <div className="bnav-icon">{item.icon}</div>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
};

/* ── 캘린더 컴포넌트 (원본 JS renderCalendar와 동일) ── */
const CalendarScreen = ({ navigate, getScreenClass, showToast }) => {
  const [calDate, setCalDate] = useState(new Date(2026, 7, 1));
  const [selectedDateKey, setSelectedDateKey] = useState(null);

  const year = calDate.getFullYear();
  const month = calDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const startWeekday = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevMonthDays = new Date(year, month, 0).getDate();
  const today = new Date();

  // 초기 선택 날짜: 이벤트 있는 첫 날짜 또는 1일
  const resolvedSelected = selectedDateKey || (() => {
    const first = Object.keys(calendarEvents).find(key => {
      const d = new Date(key);
      return d.getFullYear() === year && d.getMonth() === month;
    });
    return first || formatDateKey(year, month, 1);
  })();

  function changeMonth(diff) {
    setCalDate(prev => {
      const d = new Date(prev);
      d.setMonth(d.getMonth() + diff);
      return d;
    });
    setSelectedDateKey(null);
  }

  function selectDate(dateKey) {
    setSelectedDateKey(dateKey);
  }

  // 이벤트 렌더링
  const selectedEvents = calendarEvents[resolvedSelected] || [];
  const [selYear, selMonth, selDay] = resolvedSelected.split('-');

  // 달력 셀 생성
  const cells = [];
  for (let i = 0; i < startWeekday; i++) {
    const dateNum = prevMonthDays - startWeekday + i + 1;
    cells.push(
      <div key={`prev-${i}`} className="cal-cell other-month">
        <div className="cal-date">{dateNum}</div>
        <div className="cal-dots" />
      </div>
    );
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const dateKey = formatDateKey(year, month, day);
    const events = calendarEvents[dateKey] || [];
    const cellDate = new Date(year, month, day);
    const isToday = today.getFullYear() === cellDate.getFullYear()
      && today.getMonth() === cellDate.getMonth()
      && today.getDate() === cellDate.getDate();
    const isSelected = resolvedSelected === dateKey;
    let cls = 'cal-cell';
    if (isToday) cls += ' today';
    if (isSelected) cls += ' selected';
    cells.push(
      <div key={`day-${day}`} className={cls} onClick={() => selectDate(dateKey)}>
        <div className="cal-date">{day}</div>
        <div className="cal-dots">
          {events.map((evt, i) => (
            <div key={i} className="cal-dot" style={{ background: evt.color }} />
          ))}
        </div>
      </div>
    );
  }
  const totalCells = startWeekday + daysInMonth;
  const nextDays = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= nextDays; i++) {
    cells.push(
      <div key={`next-${i}`} className="cal-cell other-month">
        <div className="cal-date">{i}</div>
        <div className="cal-dots" />
      </div>
    );
  }

  return (
    <div className={getScreenClass('s-calendar')} id="s-calendar">
      <div className="topbar">
        <div className="tb-title" style={{ flex: 1 }}>캘린더</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => changeMonth(-1)} style={{ width: '30px', height: '30px', borderRadius: '9px', border: '1.5px solid var(--c-border)', background: 'var(--c-surface)', cursor: 'pointer', fontSize: '14px' }}>‹</button>
          <button onClick={() => changeMonth(1)} style={{ width: '30px', height: '30px', borderRadius: '9px', border: '1.5px solid var(--c-border)', background: 'var(--c-surface)', cursor: 'pointer', fontSize: '14px' }}>›</button>
        </div>
      </div>
      <div id="calendar-month-label" style={{ padding: '2px 14px 6px', fontSize: '13px', fontWeight: 500, color: 'var(--c-t2)' }}>
        {year}년 {month + 1}월
      </div>
      <div className="scroll-area">
        <div style={{ padding: '0 14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', marginBottom: '4px' }}>
            {['일','월','화','수','목','금','토'].map(d => (
              <div key={d} style={{ textAlign: 'center', fontSize: '11px', color: 'var(--c-t3)', fontWeight: 500, padding: '3px 0' }}>{d}</div>
            ))}
          </div>
          <div id="cal-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: '6px' }}>
            {cells}
          </div>
        </div>

        <div id="selected-date-title" style={{ padding: '14px 14px 6px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>
          {selYear}년 {Number(selMonth)}월 {Number(selDay)}일 일정
        </div>

        <div id="selected-events" style={{ padding: '0 14px 20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {selectedEvents.length === 0 ? (
            <div style={{ padding: '14px', border: '1.5px dashed var(--c-border)', borderRadius: '13px', fontSize: '13px', color: 'var(--c-t2)', background: '#FAFAF8' }}>
              이 날짜에는 등록된 일정이 없어요.
            </div>
          ) : (
            selectedEvents.map((event, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', padding: '12px 13px', border: '1.5px solid var(--c-border)', borderRadius: '13px', background: 'var(--c-surface)' }}>
                <div style={{ width: '4px', borderRadius: '2px', background: event.color, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-t1)' }}>{event.title}</div>
                  <div style={{ fontSize: '11px', color: 'var(--c-t2)', marginTop: '4px' }}>{event.desc}</div>
                  <div style={{ display: 'inline-block', marginTop: '6px', fontSize: '10px', fontWeight: 500, padding: '2px 8px', borderRadius: '8px', background: '#F5F4F0', color: 'var(--c-t2)' }}>
                    {event.type}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      <BottomNav active="s-calendar" navigate={navigate} />
    </div>
  );
};

/* ══════════════════════════════
   메인 앱 컴포넌트
══════════════════════════════ */
export default function UniGuideApp() {
  const [current, setCurrent] = useState('s-home');
  const [prev, setPrev] = useState(null);
  const [historyStack, setHistoryStack] = useState(['s-home']);
  const [toastMsg, setToastMsg] = useState('');
  const [toastVisible, setToastVisible] = useState(false);
  const toastTimer = useRef(null);

  // 단계 체크 상태 (원본 HTML과 동일: 1,2번 checked, 3번 current)
  const [steps, setSteps] = useState([
    { id: 1, text: '여권 원본 + 사본 1부', sub: '유효기간 6개월 이상', checked: true, current: false },
    { id: 2, text: '외국인등록증 원본', sub: '', checked: true, current: false },
    { id: 3, text: '재학증명서 (영문) 발급', sub: '포털 → 증명서 발급 → 영문 재학증명서', checked: false, current: true },
    { id: 4, text: '수수료 60,000원 준비', sub: '', checked: false, current: false },
    { id: 5, text: '출입국관리사무소 방문 예약', sub: 'Hi Korea에서 사전 예약 필수', checked: false, current: false },
    { id: 6, text: '방문 접수 및 수령', sub: '처리 기간 약 5~7 영업일', checked: false, current: false },
  ]);

  // 토글 스위치 상태
  const [toggles, setToggles] = useState({ visa: true, house: true, insurance: false });

  // 언어 카드
  const [langs, setLangs] = useState({ ko: true, zh: true, en: false, vi: false });

  // 비자 칩
  const [visaChip, setVisaChip] = useState('D-2 학생');

  // 인포 패널 (비자 채널) — 원본 JS: infoOpen = true 로 시작
  const [infoOpen, setInfoOpen] = useState(true);

  // 검색 필터 (원본 HTML: 전체 active + #연장 active)
  const [activeFilter, setActiveFilter] = useState('전체');
  const [activeFilter2, setActiveFilter2] = useState('#연장');

  // 채널 메인 필터
  const [channelFilter, setChannelFilter] = useState('전체');

  const checkedCount = steps.filter(s => s.checked).length;
  const total = steps.length;
  const pct = Math.round(checkedCount / total * 100);
  const grp1Checked = steps.slice(0, 4).filter(s => s.checked).length;
  const grp2Checked = steps.slice(4).filter(s => s.checked).length;

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

  // 원본 JS toggleStep과 동일 로직
  function toggleStep(id) {
    setSteps(prev => {
      const updated = prev.map(s => {
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

  function getScreenClass(id) {
    if (id === current) return 'screen active';
    if (id === prev) return 'screen exit-left';
    return 'screen';
  }

  // CSS 주입
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

      {/* ══════ SCREENS ══════ */}
      <div className="screens">

        {/* ① HOME */}
        <div className={getScreenClass('s-home')} id="s-home">
          <div className="topbar">
            <div className="notif-btn" onClick={() => navigate('notif-placeholder')}>
              <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: 'var(--c-bg)', border: '1.5px solid var(--c-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' }}>🔔</div>
              <div className="notif-bubble">2</div>
            </div>
            <div style={{ flex: 1, marginLeft: '8px' }}>
              <div className="tb-title">UniGuide</div>
              <div className="tb-sub">안녕하세요, Wei!</div>
            </div>
            <div onClick={() => navigate('s-profile')} style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--c-accent-l)', border: '2px solid var(--c-accent-m)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 700, color: 'var(--c-accent)', cursor: 'pointer' }}>W</div>
          </div>
          <div className="info-chip urgent">
            🛂 D-2 비자 만료까지 <strong>87일</strong> 남았습니다
          </div>
          <div className="scroll-area">
            <div className="sec-lbl">내 채널</div>
            <div className="ch-item" onClick={() => navigate('s-visa')}>
              <div className="ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
              <div className="ch-body">
                <div className="ch-name">비자 & 체류</div>
                <div className="ch-preview">비자 연장하려면 뭐가 필요해요?</div>
              </div>
              <div className="ch-meta">
                <div className="ch-time">방금</div>
                <div className="badge" style={{ background: 'var(--c-red-l)', color: 'var(--c-red)' }}>D-87</div>
              </div>
            </div>
            <div className="ch-item" onClick={() => navigate('s-main')}>
              <div className="ch-icon" style={{ background: 'var(--c-green-l)' }}>🏫</div>
              <div className="ch-body">
                <div className="ch-name">학교생활</div>
                <div className="ch-preview">수강신청은 어떻게 하나요?</div>
              </div>
              <div className="ch-meta"><div className="ch-time">어제</div></div>
            </div>
            <div className="ch-item" onClick={() => navigate('s-main')}>
              <div className="ch-icon" style={{ background: 'var(--c-amber-l)' }}>💼</div>
              <div className="ch-body">
                <div className="ch-name">취업 & 아르바이트</div>
                <div className="ch-preview">시간제 취업 허가 절차 안내 완료</div>
              </div>
              <div className="ch-meta">
                <div className="ch-time">3일 전</div>
                <div className="badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>새 답변</div>
              </div>
            </div>
            <div className="ch-item" onClick={() => navigate('s-main')}>
              <div className="ch-icon" style={{ background: 'var(--c-accent-l)' }}>🏠</div>
              <div className="ch-body">
                <div className="ch-name">주거</div>
                <div className="ch-preview">계약 만료 60일 전 알림 설정됨</div>
              </div>
              <div className="ch-meta"><div className="ch-time">1주 전</div></div>
            </div>
            <div className="ch-item" onClick={() => navigate('s-main')}>
              <div className="ch-icon" style={{ background: '#FEE2E2' }}>🏥</div>
              <div className="ch-body">
                <div className="ch-name">병원 & 보험</div>
                <div className="ch-preview">건강보험 가입 완료</div>
              </div>
              <div className="ch-meta"><div className="ch-time">2주 전</div></div>
            </div>
            <div className="sec-lbl">채널 추가</div>
            <div className="ch-item" onClick={() => showToast('채널 생성 화면으로 이동합니다')}>
              <div className="ch-icon" style={{ background: 'var(--c-bg)', border: '1.5px dashed var(--c-border-s)', fontSize: '22px' }}>+</div>
              <div className="ch-body">
                <div className="ch-name" style={{ color: 'var(--c-t2)' }}>새 채널 만들기</div>
                <div className="ch-preview">생활정보, 커뮤니티 등</div>
              </div>
            </div>
            <div style={{ height: '20px' }} />
          </div>
          <BottomNav active="s-home" navigate={navigate} />
        </div>

        {/* ② VISA CHANNEL */}
        <div className={getScreenClass('s-visa')} id="s-visa">
          <div className="slim-header">
            <div className="tb-back" onClick={back}>
              <BackIcon />
            </div>
            <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="slim-ch-name">비자 & 체류</div>
            <div className="slim-rag">RAG 활성</div>
            <div className="slim-d87" onClick={() => setInfoOpen(o => !o)}>
              <span id="d87-txt">D-87</span>
              <span id="d87-arrow" style={{ fontSize: '10px' }}>{infoOpen ? '▾' : '▸'}</span>
            </div>
          </div>
          {infoOpen && (
            <div className="info-panel" id="info-panel">
              <div className="i-chip">🗓 D-2 만료 <strong>2026. 8. 15</strong></div>
              <div className="i-chip green">🔔 알림 설정됨</div>
            </div>
          )}
          <div className="qa-scroll">
            <button className="qa-btn" onClick={() => navigate('s-step')}>📋 비자 연장 절차</button>
            <button className="qa-btn" onClick={() => showToast('외국인등록증 재발급 안내를 불러옵니다')}>🪪 외국인등록증</button>
            <button className="qa-btn" onClick={() => showToast('체류확인서 발급 안내를 불러옵니다')}>📄 체류확인서</button>
            <button className="qa-btn" onClick={() => showToast('비자 변경 절차 안내를 불러옵니다')}>🔄 비자 변경</button>
          </div>
          <div className="scroll-area">
            <div className="chat-area" id="visa-chat-area">
              <div className="msg-ai">
                <div className="ai-av">AI</div>
                <div className="bubble-ai">D-2 채널입니다. 만료까지 <strong>87일</strong> 남았어요. 위 버튼을 탭하거나 직접 질문해주세요!</div>
              </div>
            </div>
            <div style={{ height: '8px' }} />
          </div>
          <div className="chat-input-bar">
            <input className="c-input" id="visa-input" placeholder="비자 관련 질문하기..." />
            <button className="send-btn" onClick={() => showToast('메시지를 전송합니다')}>
              <SendIcon />
            </button>
          </div>
        </div>

        {/* ③ STEP GUIDE */}
        <div className={getScreenClass('s-step')} id="s-step">
          <div className="topbar">
            <div className="tb-back" onClick={back}>
              <BackIcon />
              비자 채널
            </div>
          </div>
          <div style={{ padding: '12px 16px 4px' }}>
            <div className="tb-title" style={{ fontSize: '17px' }}>D-2 비자 연장 절차</div>
            <div className="tb-sub">출입국관리사무소 방문 기준</div>
          </div>
          <div className="progress-wrap">
            <div className="progress-bg">
              <div className="progress-fill" id="prog-fill" style={{ width: `${pct}%` }} />
            </div>
            <div className="prog-label">
              <span id="prog-txt">{checkedCount} / {total} 단계 완료</span>
              <span id="prog-pct" style={{ color: 'var(--c-green)' }}>{pct}%</span>
            </div>
          </div>
          <div className="scroll-area" style={{ paddingBottom: '12px' }}>
            <div className="step-card">
              <div className="step-card-hdr">
                <span>📁 서류 준비</span>
                <span id="grp1-prog" style={{ fontSize: '11px', fontWeight: 400 }}>{grp1Checked}/4 완료</span>
              </div>
              {steps.slice(0, 4).map(step => (
                <div key={step.id} className="step-row" onClick={() => toggleStep(step.id)}>
                  <div className={`step-cb${step.checked ? ' checked' : step.current ? ' current' : ''}`}>
                    {step.checked ? '✓' : ''}
                  </div>
                  <div className="step-label">
                    <div className={`step-text${step.checked ? ' done' : ''}`} style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}>
                      {step.text}
                    </div>
                    {step.sub && (
                      <div className={`step-sub${step.checked ? ' done' : ''}`} style={!step.checked && !step.current ? { color: 'var(--c-t3)' } : {}}>
                        {step.sub}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="step-card">
              <div className="step-card-hdr">
                <span>📋 신청</span>
                <span style={{ fontSize: '11px', fontWeight: 400 }}>{grp2Checked}/2 완료</span>
              </div>
              {steps.slice(4).map(step => (
                <div key={step.id} className="step-row" onClick={() => toggleStep(step.id)}>
                  <div className={`step-cb${step.checked ? ' checked' : ''}`}>
                    {step.checked ? '✓' : ''}
                  </div>
                  <div className="step-label">
                    <div className={`step-text${step.checked ? ' done' : ''}`} style={{ color: step.checked ? undefined : 'var(--c-t3)' }}>
                      {step.text}
                    </div>
                    {step.sub && (
                      <div className={`step-sub${step.checked ? ' done' : ''}`} style={{ color: step.checked ? undefined : 'var(--c-t3)' }}>
                        {step.sub}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="save-note">✅ 체크 상태는 자동 저장됩니다. 앱을 닫아도 유지돼요.</div>
            <div style={{ margin: '4px 14px' }}>
              <button className="qa-btn" style={{ width: '100%', textAlign: 'left', borderRadius: '11px', padding: '12px 14px' }} onClick={() => showToast('주의사항을 불러옵니다')}>⚠️ 주의사항 더 보기</button>
            </div>
          </div>
        </div>

        {/* ④ MAIN CHAT */}
        <div className={getScreenClass('s-main')} id="s-main">
          <div className="topbar">
            <div className="tb-back" onClick={back}>
              <BackIcon />
            </div>
            <div>
              <div className="tb-title">메인 채팅</div>
              <div className="tb-sub">모든 채널에 질문하기</div>
            </div>
          </div>
          <div className="scroll-area">
            <div style={{ padding: '10px 14px 6px', fontSize: '11px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.6px', textTransform: 'uppercase' }}>
              케이스 A · 1차 답변 가능
            </div>
            <div className="chat-area" style={{ paddingTop: '4px' }}>
              <div className="msg-user">
                <div className="bubble-user">외국인은 알바 어떻게 해요?</div>
              </div>
            </div>
            <div className="ans-wrap">
              <div className="ans-domain" style={{ background: 'var(--c-amber-l)' }}>
                <div className="ans-dot" style={{ background: 'var(--c-amber)' }} />
                <span style={{ color: 'var(--c-amber)', fontWeight: 600 }}>취업 & 아르바이트</span>
              </div>
              <div className="ans-body">D-2 유학생은 <strong>시간제 취업 허가</strong> 후 주 20시간 이내 알바 가능합니다.</div>
              <div className="ans-tags">
                <span className="tag" style={{ background: 'var(--c-amber-l)', color: 'var(--c-amber)' }}>#취업</span>
                <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#비자</span>
              </div>
            </div>
            <div className="cta-card" onClick={() => navigate('s-channel-main')} style={{ marginTop: '8px' }}>
              <div className="cta-icon" style={{ background: 'var(--c-amber-l)' }}>💼</div>
              <div className="cta-body">
                <div className="cta-title">채널에서 자세히 보기</div>
                <div className="cta-sub">허가 절차 · 학교 규정 · Step-by-step</div>
              </div>
              <div className="cta-arrow">›</div>
            </div>

            <div style={{ margin: '16px 14px 10px', height: '1px', background: 'var(--c-border)' }} />

            <div style={{ padding: '0 14px 6px', fontSize: '11px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.6px', textTransform: 'uppercase' }}>
              케이스 B · 1차 답변 불가
            </div>
            <div className="chat-area" style={{ paddingTop: '4px' }}>
              <div className="msg-user">
                <div className="bubble-user">건강보험 외국인 특례 3조 내용이 뭐예요?</div>
              </div>
              <div className="msg-ai">
                <div className="ai-av">AI</div>
                <div className="bubble-ai" style={{ color: 'var(--c-t2)', fontSize: '13px' }}>이 질문은 <strong style={{ color: 'var(--c-t1)' }}>병원 & 보험</strong> 채널에서 정확하게 답변드릴 수 있어요.</div>
              </div>
            </div>
            <div className="cta-card neutral" onClick={() => showToast('병원 & 보험 채널로 이동합니다')}>
              <div className="cta-icon" style={{ background: '#FEE2E2' }}>🏥</div>
              <div className="cta-body">
                <div className="cta-title">병원 & 보험 채널에서 답변 받기</div>
                <div className="cta-sub">건강보험 전용 RAG로 정확한 답변</div>
              </div>
              <div className="cta-arrow">›</div>
            </div>
            <div id="main-chat-area" className="chat-area" style={{ paddingTop: 0 }} />
            <div style={{ height: '16px' }} />
          </div>
          <div className="chat-input-bar">
            <input id="main-input" className="c-input" placeholder="무엇이든 질문하세요..." />
            <button className="send-btn" onClick={() => showToast('메시지를 전송합니다')}>
              <SendIcon />
            </button>
          </div>
          <BottomNav active="s-main" navigate={navigate} />
        </div>

        {/* ⑤ CALENDAR */}
        <CalendarScreen navigate={navigate} getScreenClass={getScreenClass} showToast={showToast} />

        {/* ⑥ CHANNEL MAIN (지식 카드) */}
        <div className={getScreenClass('s-channel-main')} id="s-channel-main">
          <div className="slim-header">
            <div className="tb-back" onClick={back}><BackIcon /></div>
            <div className="slim-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
            <div className="slim-ch-name">비자 & 체류</div>
            <div className="slim-rag">RAG 활성</div>
          </div>
          <div className="ch-tabs">
            <div className="ch-tab" onClick={() => navigate('s-visa')}>💬 채팅</div>
            <div className="ch-tab active">📚 지식 카드</div>
          </div>
          <div className="search-bar">
            <SearchIcon />
            <span>채널 내 대화 검색...</span>
          </div>
          <div className="filter-row">
            {['전체','#연장','#D-2','#서류','#출입국'].map(f => (
              <button key={f} className={`filter-chip${channelFilter === f ? ' active' : ''}`} onClick={() => { setChannelFilter(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
            ))}
          </div>
          <div className="scroll-area" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px 0 12px' }}>
            <div className="k-card" onClick={() => navigate('s-knowledge')}>
              <div className="k-card-body">
                <div className="k-q">비자 연장하려면 뭐가 필요해요?</div>
                <div className="k-preview">D-2 비자 연장 서류입니다. ① 여권 원본 ② 외국인등록증 ③ 재학증명서 (영문)...</div>
              </div>
              <div className="k-card-foot">
                <div style={{ display: 'flex', gap: '5px' }}>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#서류</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>3일 전</span>
              </div>
            </div>
            <div className="k-card" onClick={() => navigate('s-knowledge')}>
              <div className="k-card-body">
                <div className="k-q">비자 연장 신청 기간이 언제예요?</div>
                <div className="k-preview">만료일 4개월 전부터 신청 가능합니다. 늦어도 만료 1개월 전에는...</div>
              </div>
              <div className="k-card-foot">
                <div style={{ display: 'flex', gap: '5px' }}>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#기간</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>1주 전</span>
              </div>
            </div>
            <div className="k-card" onClick={() => navigate('s-knowledge')}>
              <div className="k-card-body">
                <div className="k-q">Hi Korea에서 온라인 신청이 가능한가요?</div>
                <div className="k-preview">네, Hi Korea(www.hikorea.go.kr)에서 온라인으로 비자 연장 신청이 가능합니다...</div>
              </div>
              <div className="k-card-foot">
                <div style={{ display: 'flex', gap: '5px' }}>
                  <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#출입국</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--c-t3)' }}>2주 전</span>
              </div>
            </div>
          </div>
        </div>

        {/* ⑦ KNOWLEDGE DETAIL */}
        <div className={getScreenClass('s-knowledge')} id="s-knowledge">
          <div className="topbar">
            <div className="tb-back" onClick={back}><BackIcon /></div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
              <div style={{ width: '24px', height: '24px', borderRadius: '7px', background: 'var(--c-purple-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px' }}>🛂</div>
              <span style={{ fontSize: '13px', color: 'var(--c-t2)' }}>비자 & 체류 채널</span>
            </div>
          </div>
          <div className="scroll-area">
            <div className="kd-q-box">
              <div className="kd-q-label">Q. 원본 질문</div>
              <div className="kd-q-text">비자 연장하려면 뭐가 필요해요?</div>
            </div>
            <div style={{ padding: '8px 14px 6px', display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
              <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#서류</span>
              <span style={{ fontSize: '11px', color: 'var(--c-t3)', display: 'flex', alignItems: 'center', marginLeft: '4px' }}>3일 전</span>
            </div>
            <div className="kd-block-text">D-2 비자 연장에 필요한 서류입니다. 출입국관리사무소 방문 신청 또는 Hi Korea 온라인 신청 모두 가능합니다.</div>
            <div className="kd-list-block">
              <div className="kd-list-title">📋 필요 서류</div>
              {[
                '여권 원본 + 사본 1부 (유효기간 6개월 이상)',
                '외국인등록증 원본',
                '재학증명서 (영문)',
                '수수료 60,000원',
              ].map((item, i) => (
                <div key={i} className="kd-list-item">
                  <div className="kd-num">{i + 1}</div>{item}
                </div>
              ))}
            </div>
            <div className="kd-source">📎 출처: 법무부 출입국관리법 시행규칙 (2024) · Hi Korea 외국인 안내</div>
            <div className="kd-section-lbl">⚡ Action Guide</div>
            <div className="cta-card" onClick={() => navigate('s-step')} style={{ margin: '0 14px 14px' }}>
              <div className="cta-icon">📋</div>
              <div className="cta-body">
                <div className="cta-title">비자 연장 절차 보기</div>
                <div className="cta-sub">6단계 체크리스트 · 진행 현황 추적</div>
              </div>
              <div className="cta-arrow">›</div>
            </div>
            <div className="kd-section-lbl">🔗 관련 질문</div>
            <div className="related-q" onClick={() => showToast('관련 질문을 불러옵니다')}>
              비자 연장 신청 기간이 언제예요?
              <span style={{ color: 'var(--c-t3)', fontSize: '18px' }}>›</span>
            </div>
            <div className="related-q" onClick={() => showToast('관련 질문을 불러옵니다')}>
              Hi Korea 온라인 신청이 가능한가요?
              <span style={{ color: 'var(--c-t3)', fontSize: '18px' }}>›</span>
            </div>
            <div style={{ height: '16px' }} />
          </div>
        </div>

        {/* ⑧ ONBOARDING */}
        <div className={getScreenClass('s-onboarding')} id="s-onboarding">
          <div style={{ flex: 1, overflowY: 'auto', WebkitOverflowScrolling: 'touch' }}>
            <div className="ob-hero">
              <span className="ob-mark">🎓</span>
              <div className="ob-h">UniGuide AI</div>
              <div className="ob-p">한국 유학 생활, 더 쉽게<br />비자·학교·생활 모두 안내해드려요</div>
            </div>
            <button className="social-btn" onClick={() => showToast('Google 로그인 화면으로 이동합니다')}>
              <span style={{ fontSize: '18px' }}>🌐</span> Google로 시작하기
            </button>
            <div style={{ padding: '0 16px 12px', textAlign: 'center', fontSize: '12px', color: 'var(--c-t3)' }}>카카오 로그인은 추후 지원 예정입니다</div>
            <div style={{ height: '1px', background: 'var(--c-border)', margin: '0 0 16px' }} />
            <div className="ob-steps">
              <div className="ob-step-dot done" />
              <div className="ob-step-dot active" />
              <div className="ob-step-dot" />
            </div>
            <div className="form-sec">기본 정보 입력</div>
            <div className="form-note">국적·학교·비자 유형만 입력하면 바로 시작할 수 있어요</div>
            <div className="form-group" style={{ marginTop: '8px' }}>
              <div className="f-label">국적</div>
              <div className="f-input filled">🇨🇳 중국 <span style={{ color: 'var(--c-t3)' }}>▾</span></div>
            </div>
            <div className="form-group">
              <div className="f-label">학교</div>
              <div className="f-input filled">부산대학교</div>
            </div>
            <div className="form-group">
              <div className="f-label">비자 유형</div>
              <div className="chip-row">
                {['D-2 학생', 'D-4 어학연수', 'F-2 거주', '기타'].map(v => (
                  <button key={v} className={`sel-chip${visaChip === v ? ' on' : ''}`} onClick={() => setVisaChip(v)}>{v}</button>
                ))}
              </div>
            </div>
            <div className="ob-note">📅 비자 만료일은 비자 채널에서 대화할 때 입력할 수 있어요</div>
            <div className="form-sec">사용 언어</div>
            <div className="lang-grid">
              {[['ko','🇰🇷','한국어','Korean'],['zh','🇨🇳','중국어','Chinese'],['en','🇺🇸','영어','English'],['vi','🇻🇳','베트남어','Vietnamese']].map(([key,flag,name,sub]) => (
                <div key={key} className={`lang-card${langs[key] ? ' on' : ''}`} onClick={() => setLangs(l => ({ ...l, [key]: !l[key] }))}>
                  <div className="lang-flag">{flag}</div>
                  <div className="lang-name">{name}</div>
                  <div className="lang-sub">{sub}</div>
                </div>
              ))}
            </div>
            <button className="cta-primary" onClick={() => navigate('s-home')}>시작하기 →</button>
            <div className="footnote">국적·학교·비자 유형만으로 맞춤 채널이 자동 생성됩니다</div>
          </div>
        </div>

        {/* ⑨ SEARCH */}
        <div className={getScreenClass('s-search')} id="s-search">
          <div className="topbar">
            <div className="tb-title" style={{ flex: 1 }}>검색</div>
            <div className="tb-sub" style={{ fontSize: '11px', color: 'var(--c-t3)' }}>과거 대화 전체 탐색</div>
          </div>
          <div className="search-bar" style={{ marginTop: '6px' }}>
            <SearchIcon />
            <span>비자 연장</span>
          </div>
          <div className="filter-row">
            {['전체','🛂 비자','🏫 학교','💼 취업','🏠 주거'].map(f => (
              <button key={f} className={`filter-chip${activeFilter === f ? ' active' : ''}`} onClick={() => { setActiveFilter(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
            ))}
          </div>
          <div className="filter-row" style={{ paddingTop: 0 }}>
            {['#연장','#D-2','#서류','#출입국'].map(f => (
              <button key={f} className={`filter-chip${activeFilter2 === f ? ' active' : ''}`} style={{ fontSize: '11px' }} onClick={() => { setActiveFilter2(f); showToast(f + ' 필터가 적용됐습니다'); }}>{f}</button>
            ))}
          </div>
          <div style={{ padding: '4px 14px 8px', fontSize: '12px', fontWeight: 600, color: 'var(--c-t3)', letterSpacing: '.5px' }}>검색 결과 2건</div>
          <div className="scroll-area" style={{ paddingBottom: '12px' }}>
            <div className="result-card" onClick={() => navigate('s-knowledge')}>
              <div className="result-inner">
                <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
                <div className="result-body">
                  <div className="result-q">비자 연장하려면 뭐가 필요해요?</div>
                  <div className="result-p">D-2 비자 연장 서류입니다. ① 여권 원본 ② 외국인등록증...</div>
                  <div className="result-foot">
                    <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#D-2</span>
                    <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                    <span className="r-time">3일 전</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="result-card" onClick={() => navigate('s-knowledge')}>
              <div className="result-inner">
                <div className="result-ch-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
                <div className="result-body">
                  <div className="result-q">비자 연장 신청 기간이 언제예요?</div>
                  <div className="result-p">만료일 4개월 전부터 신청 가능합니다. 늦어도 1개월 전에...</div>
                  <div className="result-foot">
                    <span className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>#연장</span>
                    <span className="r-time">1주 전</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <BottomNav active="s-search" navigate={navigate} />
        </div>

        {/* ⑩ PROFILE */}
        <div className={getScreenClass('s-profile')} id="s-profile">
          <div className="topbar">
            <div className="tb-title">내 정보</div>
          </div>
          <div className="scroll-area">
            <div className="profile-hero">
              <div className="p-av">W</div>
              <div className="p-name">Wei Zhang</div>
              <div className="p-school">부산대학교 · 컴퓨터공학과 3학년</div>
              <div className="p-badges">
                <span className="p-badge" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>🛂 D-2 비자</span>
                <span className="p-badge" style={{ background: 'var(--c-accent-l)', color: 'var(--c-accent)' }}>🇨🇳 중국</span>
                <span className="p-badge" style={{ background: 'var(--c-red-l)', color: 'var(--c-red)' }}>D-87</span>
              </div>
            </div>
            <div className="visa-card">
              <div className="vc-hdr">🛂 비자 정보</div>
              <div className="vc-row">
                <div className="vc-label">비자 유형</div>
                <div className="vc-val">D-2 (학생)</div>
              </div>
              <div className="vc-row">
                <div className="vc-label">만료일</div>
                <div className="vc-val" style={{ color: 'var(--c-red)' }}>2026. 8. 15 (D-87)</div>
              </div>
              <div className="vc-btn" onClick={() => showToast('비자 정보 수정 화면으로 이동합니다')}>비자 정보 수정</div>
            </div>
            <div className="setting-sec">알림 설정</div>
            <div className="setting-row">
              <div className="s-icon" style={{ background: 'var(--c-purple-l)' }}>🛂</div>
              <div className="s-body">
                <div className="s-name">비자 & 체류 알림</div>
                <div className="s-val">만료 90일·30일·7일 전</div>
              </div>
              <div className={`toggle-track ${toggles.visa ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, visa: !t.visa })); showToast(toggles.visa ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
                <div className="toggle-knob" />
              </div>
            </div>
            <div className="setting-row">
              <div className="s-icon" style={{ background: 'var(--c-amber-l)' }}>🏠</div>
              <div className="s-body">
                <div className="s-name">주거 계약 알림</div>
                <div className="s-val">만료 60일 전</div>
              </div>
              <div className={`toggle-track ${toggles.house ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, house: !t.house })); showToast(toggles.house ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
                <div className="toggle-knob" />
              </div>
            </div>
            <div className="setting-row">
              <div className="s-icon" style={{ background: 'var(--c-green-l)' }}>🏥</div>
              <div className="s-body">
                <div className="s-name">보험료 납부 알림</div>
                <div className="s-val">납부일 5일 전</div>
              </div>
              <div className={`toggle-track ${toggles.insurance ? 'on' : 'off'}`} onClick={() => { setToggles(t => ({ ...t, insurance: !t.insurance })); showToast(toggles.insurance ? '알림이 꺼졌습니다' : '알림이 켜졌습니다'); }}>
                <div className="toggle-knob" />
              </div>
            </div>
            <div className="setting-sec">앱 설정</div>
            <div className="setting-row" onClick={() => showToast('언어 설정 화면으로 이동합니다')}>
              <div className="s-icon" style={{ background: 'var(--c-accent-l)' }}>🌐</div>
              <div className="s-body">
                <div className="s-name">사용 언어</div>
                <div className="s-val">한국어 · 中文</div>
              </div>
              <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
            </div>
            <div className="setting-row" onClick={() => showToast('개인정보 수정 화면으로 이동합니다')}>
              <div className="s-icon" style={{ background: 'var(--c-bg)' }}>👤</div>
              <div className="s-body">
                <div className="s-name">개인정보 수정</div>
                <div className="s-val">이름, 학교, 학과</div>
              </div>
              <div style={{ fontSize: '18px', color: 'var(--c-t3)' }}>›</div>
            </div>
            <div className="logout-btn" onClick={() => navigate('s-onboarding')}>로그아웃</div>
            <div style={{ height: '20px' }} />
          </div>
          <BottomNav active="s-profile" navigate={navigate} />
        </div>

      </div>{/* /screens */}

      {/* Toast */}
      <div className={`toast${toastVisible ? ' show' : ''}`}>{toastMsg}</div>
    </div>
  );
}