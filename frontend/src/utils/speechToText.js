/**
 * src/utils/speechToText.js
 * ─────────────────────────────────────────────
 * 음성 입력(STT) 연결 지점 — 채팅 입력창 옆 🎙️ 버튼이 이 파일만 호출한다.
 *
 * 현재: 미연결 (STT_READY = false) → 버튼을 누르면 "곧 지원될 예정" 토스트만 뜬다.
 *
 * STT 연결하는 방법 (담당 팀원용)
 *   1. recognizeSpeech() 안에 실제 인식 로직을 구현한다
 *      (브라우저 Web Speech API, 백엔드 STT 엔드포인트 등 무엇이든 OK)
 *   2. STT_READY 를 true 로 바꾼다
 *   → 인식된 문장이 입력창에 채워지고, 사용자가 확인 후 직접 전송한다.
 *     (ChatInput.jsx 는 수정할 필요 없음)
 */

/** STT 가 연결됐는지 여부 */
export const STT_READY = false;

/**
 * 음성을 듣고 인식된 문장을 돌려준다.
 *
 * @param {object} options
 * @param {string} options.lang — 현재 앱 언어의 BCP-47 태그 (예: 'ko-KR', 'zh-CN', 'en-US')
 * @returns {Promise<string>} 인식된 텍스트
 */
// eslint-disable-next-line no-unused-vars
export async function recognizeSpeech({ lang }) {
  throw new Error('STT 가 아직 연결되지 않았습니다');
}
