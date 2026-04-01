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
  // 퇴장 애니메이션 트리거 상태
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    // 3.6s 후 퇴장 애니메이션 시작 (CSS .exiting 클래스 적용)
    const exitTimer = setTimeout(() => setExiting(true), 3600);

    // 4.2s 후 onFinish 호출 → 부모에서 컴포넌트 언마운트
    const doneTimer = setTimeout(() => {
      if (onFinish) onFinish();
    }, 4200);

    // 컴포넌트 언마운트 시 타이머 정리
    return () => {
      clearTimeout(exitTimer);
      clearTimeout(doneTimer);
    };
  }, [onFinish]);

  return (
    /* exiting 클래스가 붙으면 scale-up + fade-out 애니메이션 실행 */
    <div className={`splash-screen${exiting ? ' exiting' : ''}`}>

      {/* ── 배경 반짝이 파티클 ──────────────────────────────────────── */}
      {/* 각 star는 CSS animation-delay로 시간차 트윙클 효과 */}
      <div className="splash-stars">
        <span className="star star-1" />
        <span className="star star-2" />
        <span className="star star-3" />
        <span className="star star-4" />
        <span className="star star-5" />
      </div>

      <div className="splash-content">

        {/* ── 브랜드 텍스트 ──────────────────────────────────────────── */}
        {/* brand-title: 0.4s delay → 위로 떠오르며 등장  */}
        {/* brand-subtitle: 0.9s delay → 뒤따라 등장      */}
        <div className="brand-wrap">
          <h1 className="brand-title">YUHAKSEAG</h1>
          <p className="brand-subtitle">당신의 유학생 생활을 안내합니다</p>
        </div>

        {/* ── 글로브 씬 ──────────────────────────────────────────────── */}
        {/* scenePop 애니메이션으로 전체 씬이 scale 0.82 → 1 등장       */}
        <div className="globe-scene">

          {/* 궤도 링 (장식) ─────────────────────────────────────────── */}
          {/* orbit-back: 반투명 전체 타원 선                            */}
          {/* orbit-front: 하단 절반만 밝게 — 입체감 표현               */}
          <div className="orbit orbit-back" />
          <div className="orbit orbit-front" />

          {/* 비행기 궤도 래퍼 ────────────────────────────────────────── */}
          {/* orbitSpin 키프레임: rotate(-18deg)를 기준으로 360° 회전   */}
          {/* plane은 래퍼 오른쪽 끝(left:100%)에 고정 → 공전처럼 보임 */}
          <div className="plane-orbit">
            <div className="plane">
              {/* plane-body: ✈️ 이모지 + 궤도 기울기 보정 rotate(18deg) */}
              <div className="plane-body">✈️</div>
              {/* plane-glow: 비행기 아래 흐릿한 빛 번짐 효과            */}
              <div className="plane-glow" />
            </div>
          </div>

          {/* 글로브 ─────────────────────────────────────────────────── */}
          {/* globeFloat 키프레임: translateY 0 → -8px 무한 반복 (둥둥) */}
          <div className="globe">
            {/* 좌상단 반사광 하이라이트 */}
            <div className="globe-shine" />

            {/* 구름 레이어 (흰색 pill 형태) */}
            <div className="globe-cloud cloud-1" />
            <div className="globe-cloud cloud-2" />

            {/* 대륙 레이어 (border-radius로 유기적 형태 표현) */}
            <div className="continent continent-1" />  {/* 좌측 큰 대륙 */}
            <div className="continent continent-2" />  {/* 우측 작은 대륙 */}
            <div className="continent continent-3" />  {/* 하단 대륙 */}
          </div>

        </div>
      </div>
    </div>
  );
}
