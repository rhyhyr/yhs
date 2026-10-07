/**
 * src/i18n/core.js
 * ─────────────────────────────────────────────
 * React 밖에서도 쓸 수 있는 i18n 코어 (mock 데이터·api 레이어용).
 * 컴포넌트에서는 i18n/index.jsx 의 useI18n() 을 사용하세요.
 *
 * 새 언어 추가 방법 (예: 베트남어)
 *   1. locales/xx.js 를 만든다 (ko.js 와 같은 구조, meta 포함)
 *   2. 아래 LOCALES 에 등록한다 (중국어는 이미 등록됨)
 *   → 설정 화면의 언어 선택 목록에 자동으로 나타난다.
 *
 * 번역 조회 규칙
 *   t(key)         UI 문구. 현재 언어 → ko → key 순으로 찾는다.
 *   tx(key, base)  데이터(체크리스트·채널·mock 응답)의 번역본.
 *                  현재 언어에 키가 없으면 데이터에 원래 들어 있던 base(한국어)를 쓴다.
 */
import ko from './locales/ko';
import en from './locales/en';
import zh from './locales/zh';

export const LOCALES = { ko, en, zh };
export const DEFAULT_LOCALE = 'ko';

const STORAGE_KEY = 'uniguide.locale';

function loadLocale() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && LOCALES[saved]) return saved;
  } catch { /* localStorage 접근 불가 — 기본값 사용 */ }
  return DEFAULT_LOCALE;
}

let current = loadLocale();

export function getLocale() {
  return current;
}

export function setLocaleCore(code) {
  if (!LOCALES[code]) return;
  current = code;
  try { localStorage.setItem(STORAGE_KEY, code); } catch { /* ignore */ }
}

function lookup(dict, key) {
  let node = dict;
  for (const part of key.split('.')) {
    if (node == null || typeof node !== 'object') return undefined;
    node = node[part];
  }
  return typeof node === 'string' ? node : undefined;
}

function interpolate(str, params) {
  if (!params) return str;
  return str.replace(/\{(\w+)\}/g, (m, name) => (name in params ? params[name] : m));
}

/** UI 문구 번역 */
export function translate(key, params) {
  const str = lookup(LOCALES[current], key) ?? lookup(LOCALES[DEFAULT_LOCALE], key) ?? key;
  return interpolate(str, params);
}

/** 데이터 번역 — 번역본이 없으면 base(원문) 그대로 */
export function translateData(key, base) {
  return lookup(LOCALES[current], key) ?? base;
}
