/**
 * src/utils/googleAuth.js
 * ─────────────────────────────────────────────
 * 구글 로그인 없이(백엔드 없이) 캘린더에 직접 쓰기 위한 OAuth 토큰 발급.
 *
 * Google Identity Services(GIS)의 "토큰 모델"을 사용한다 — client secret이
 * 필요 없는 방식이라 프론트엔드에 client id를 그대로 둬도 안전하다.
 * (index.html에 <script src="https://accounts.google.com/gsi/client">가
 *  미리 로드되어 있어야 함)
 *
 * 받은 접근 토큰은 메모리에만 들고 있는다(AppContext) — 약 1시간 후 만료되며,
 * 백엔드 없이는 "조용한 재발급(refresh token)"이 불가능해서 만료되면
 * 사용자가 다시 연결 버튼을 눌러야 한다. (이건 백엔드 없는 방식의 본질적인
 * 한계라 의도된 동작이다.)
 */

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// 캘린더 일정 읽기/쓰기만 — 전체 캘린더 권한(calendar)보다 좁은 범위라 동의 화면에서 덜 무섭게 보임
const SCOPE = 'https://www.googleapis.com/auth/calendar.events';

let tokenClient = null;

function getTokenClient() {
  if (tokenClient) return tokenClient;
  if (!window.google?.accounts?.oauth2) {
    throw new Error('GIS_NOT_LOADED');
  }
  tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: CLIENT_ID,
    scope: SCOPE,
    // 실제 콜백은 requestGoogleAccessToken() 호출마다 아래서 덮어씀
    callback: () => {},
  });
  return tokenClient;
}

/**
 * 구글 로그인 동의 팝업을 띄우고 접근 토큰을 받아온다.
 * @returns {Promise<string>} access_token
 */
export function requestGoogleAccessToken() {
  return new Promise((resolve, reject) => {
    if (!CLIENT_ID) {
      reject(new Error('NO_CLIENT_ID'));
      return;
    }

    let client;
    try {
      client = getTokenClient();
    } catch {
      reject(new Error('GIS_NOT_LOADED'));
      return;
    }

    client.callback = (response) => {
      if (response.error) reject(new Error(response.error));
      else resolve(response.access_token);
    };

    client.requestAccessToken();
  });
}

/** 클라이언트 ID가 설정돼 있는지 (버튼 자체를 숨길지 판단용) */
export function hasGoogleClientId() {
  return Boolean(CLIENT_ID);
}
