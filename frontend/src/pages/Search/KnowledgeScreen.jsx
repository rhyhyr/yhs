import { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import { useI18n } from '../../i18n';
import { getChannel } from '../../api/channels';
import { BackIcon } from '../../components/Common/icons';
import SourceModal from '../../components/Chat/SourceModal';

const DOC_COUNT = 4;
const SOURCE_COUNT = 2;

export default function KnowledgeScreen() {
  const { navigate, back, showToast } = useApp();
  const { t, localizeChannel } = useI18n();
  const [sourceOpen, setSourceOpen] = useState(false);

  const sources = Array.from({ length: SOURCE_COUNT }, (_, i) => ({
    label: t(`kb.sources.${i}.label`),
    detail: t(`kb.sources.${i}.detail`),
  }));

  return (
    <>
      <div className="topbar">
        <div className="tb-back" onClick={back}><BackIcon /></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '7px', background: 'var(--c-purple-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px' }}>🛂</div>
          <span style={{ fontSize: '13px', color: 'var(--c-t2)' }}>{t('kb.channelLabel', { name: localizeChannel(getChannel('visa')).name })}</span>
        </div>
      </div>
      <div className="scroll-area">
        <div className="kd-q-box">
          <div className="kd-q-label">{t('kb.originalQ')}</div>
          <div className="kd-q-text">{t('kb.q1.q')}</div>
        </div>
        <div style={{ padding: '8px 14px 6px', display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          {['d2', 'extend', 'docs'].map(tag => (
            <span key={tag} className="tag" style={{ background: 'var(--c-purple-l)', color: 'var(--c-purple)' }}>{t(`tags.${tag}`)}</span>
          ))}
          <span style={{ fontSize: '11px', color: 'var(--c-t3)', display: 'flex', alignItems: 'center', marginLeft: '4px' }}>{t('time.daysAgo', { n: 3 })}</span>
        </div>
        <div className="kd-block-text">{t('kb.answerBody')}</div>
        <div className="kd-list-block">
          <div className="kd-list-title">{t('kb.requiredDocs')}</div>
          {Array.from({ length: DOC_COUNT }, (_, i) => (
            <div key={i} className="kd-list-item">
              <div className="kd-num">{i + 1}</div>{t(`kb.docs.${i}`)}
            </div>
          ))}
        </div>
        <div className="kd-source" onClick={() => setSourceOpen(true)}>
          {t('kb.sourceLine', { a: sources[0].label, b: sources[1].label })}
        </div>
        <div className="kd-section-lbl">{t('kb.actionGuide')}</div>
        <div className="cta-card" onClick={() => navigate('s-step')} style={{ margin: '0 14px 14px' }}>
          <div className="cta-icon">📋</div>
          <div className="cta-body">
            <div className="cta-title">{t('kb.ctaTitle')}</div>
            <div className="cta-sub">{t('kb.ctaSub')}</div>
          </div>
          <div className="cta-arrow">›</div>
        </div>
        <div className="kd-section-lbl">{t('kb.related')}</div>
        {['q2', 'q3'].map(key => (
          <div key={key} className="related-q" onClick={() => showToast(t('toast.relatedLoading'))}>
            {t(`kb.${key}.q`)}
            <span style={{ color: 'var(--c-t3)', fontSize: '18px' }}>›</span>
          </div>
        ))}
        <div style={{ height: '16px' }} />
      </div>

      <SourceModal
        isOpen={sourceOpen}
        onClose={() => setSourceOpen(false)}
        sources={sources}
      />
    </>
  );
}
