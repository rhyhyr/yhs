import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  LOCALES, getLocale, setLocaleCore, translate, translateData,
} from './core';

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(getLocale);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const value = useMemo(() => {
    const tag = LOCALES[locale].meta.tag;

    function setLocale(code) {
      setLocaleCore(code);
      setLocaleState(getLocale());
    }

    const t  = (key, params) => translate(key, params);
    const tx = (key, base) => translateData(key, base);

    /** 체크리스트(또는 단계 목록)의 각 항목 텍스트를 현재 언어로 */
    function localizeSteps(steps, checklistId) {
      return steps.map(s => ({
        ...s,
        text: tx(`checklists.${checklistId}.items.${s.id}.text`, s.text),
        sub:  tx(`checklists.${checklistId}.items.${s.id}.sub`, s.sub),
      }));
    }

    function localizeChecklist(cl) {
      if (!cl) return cl;
      return {
        ...cl,
        title: tx(`checklists.${cl.id}.title`, cl.title),
        type:  tx(`checklists.${cl.id}.type`, cl.type),
        items: localizeSteps(cl.items, cl.id),
      };
    }

    function localizeChannel(ch) {
      if (!ch) return ch;
      return {
        ...ch,
        name:        tx(`channels.${ch.id}.name`, ch.name),
        welcomeMsg:  tx(`channels.${ch.id}.welcome`, ch.welcomeMsg),
        placeholder: tx(`channels.${ch.id}.placeholder`, ch.placeholder),
        quickActions: (ch.quickActions ?? []).map((a, i) => ({
          ...a,
          label: tx(`channels.${ch.id}.qa.${i}.label`, a.label),
          text:  a.text && tx(`channels.${ch.id}.qa.${i}.text`, a.text),
        })),
      };
    }

    /** 날짜 서식 — Intl 이 언어별 표기(9월 21일 / September 21 / 9月21日)를 처리 */
    const fmt = (date, options) => new Intl.DateTimeFormat(tag, options).format(date);

    return {
      locale,
      setLocale,
      languages: Object.values(LOCALES).map(l => l.meta),
      t, tx, fmt,
      localizeSteps, localizeChecklist, localizeChannel,
    };
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n 은 I18nProvider 안에서만 사용할 수 있습니다.');
  return ctx;
}
