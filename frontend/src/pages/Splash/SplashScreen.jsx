import { useEffect, useState } from 'react';
import './SplashScreen.css';

/**
 * SplashScreen
 *
 * 앱 최초 진입 시 표시되는 인트로 화면.
 * 타임라인:
 *   0.0s  글로브 + 텍스트 등장 애니메이션 시작
 *   1.1s  비행기 궤도 회전 시작 (CSS animation delay)
 *   3.6s  퇴장 애니메이션 시작 (.exiting 클래스 추가 → scale-up + fade-out)
 *   4.2s  onFinish() 호출 → App.jsx에서 showSplash = false, HomeScreen 노출
 *
 * Props:
 *   onFinish {Function} — 애니메이션 완료 후 호출되는 콜백
 */
export default function SplashScreen({ onFinish }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const exitTimer = setTimeout(() => setExiting(true), 3600);
    const doneTimer = setTimeout(() => {
      if (onFinish) onFinish();
    }, 4200);

    return () => {
      clearTimeout(exitTimer);
      clearTimeout(doneTimer);
    };
  }, [onFinish]);

  return (
    <div className={`splash-screen${exiting ? ' exiting' : ''}`}>
      <div className="splash-stars">
        <span className="star star-1" />
        <span className="star star-2" />
        <span className="star star-3" />
        <span className="star star-4" />
        <span className="star star-5" />
      </div>

      <div className="splash-content">
        <div className="brand-wrap">
          <h1 className="brand-title">YUHAKSEAG</h1>
          <p className="brand-subtitle">당신의 유학생 생활을 안내합니다</p>
        </div>

        <div className="globe-scene">
          <div className="orbit orbit-back" />
          <div className="orbit orbit-front" />
          <div className="plane-orbit">
            <div className="plane">
              <div className="plane-body">✈️</div>
              <div className="plane-glow" />
            </div>
          </div>
          <div className="globe">
            <div className="globe-shine" />
            <div className="globe-cloud cloud-1" />
            <div className="globe-cloud cloud-2" />
            <div className="continent continent-1" />
            <div className="continent continent-2" />
            <div className="continent continent-3" />
          </div>
        </div>
      </div>
    </div>
  );
}
