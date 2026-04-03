/**
 * src/api/chat.js
 * ─────────────────────────────────────────────
 * 채팅 API 레이어
 *
 * 현재: mock 데이터 반환 (개발 단계)
 * 이후: 주석 처리된 fetch 블록으로 교체하면 됩니다.
 *
 * ── 백엔드 계약 (예상 엔드포인트) ──────────────────
 *
 * [sendMessage]
 * POST /api/chat
 * Request:
 *   {
 *     "channelId": "visa",
 *     "message":   "비자 연장 방법 알려주세요",
 *     "history":   [{ "role": "user", "content": "..." }, ...]
 *   }
 * Response:
 *   {
 *     "answer":  "D-2 비자 연장은 만료일 4개월 전부터...",
 *     "sources": [
 *       { "id": "src-1", "label": "법무부 출입국관리법", "detail": "제76조", "url": "" }
 *     ],
 *     "tags": ["#비자", "#연장"]
 *   }
 *
 * [getChannelMessages]
 * GET /api/channels/:channelId/messages?limit=50
 * Response:
 *   {
 *     "messages": [
 *       {
 *         "id": "visa-1712345678-ai",
 *         "channelId": "visa",
 *         "role": "ai",
 *         "text": "...",
 *         "sources": [...],
 *         "createdAt": 1712345678901
 *       }
 *     ]
 *   }
 */

import { BASE_URL } from './config';
import { pickMockResponse, createMessage } from '../data/mockMessages';

// ── 내부 상수 ────────────────────────────────────────────────────────────

/** mock 응답 딜레이 (ms) — 실제 네트워크 느낌 시뮬레이션 */
const MOCK_DELAY = 700;

// ── API 함수 ─────────────────────────────────────────────────────────────

/**
 * 채널의 이전 메시지 목록 조회
 *
 * @param {string} channelId
 * @returns {Promise<Message[]>}
 *
 * [실제 API 교체 시]
 * const res = await fetch(`${BASE_URL}/api/channels/${channelId}/messages?limit=50`);
 * if (!res.ok) throw new Error(`HTTP ${res.status}`);
 * const data = await res.json();
 * return data.messages;
 */
export async function getChannelMessages(channelId) {
  // ── mock: 빈 배열 반환 (히스토리는 AppContext에서 관리)
  await delay(0);
  return [];

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/channels/${channelId}/messages?limit=50`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.messages ?? [];
  */
}

/**
 * 사용자 메시지를 AI에게 전송하고 응답을 받습니다.
 *
 * @param {object} params
 * @param {string}   params.channelId  — 채널 ID
 * @param {string}   params.message    — 사용자 입력 텍스트
 * @param {Array}    params.history    — 이전 대화 [{ role, content }]
 * @returns {Promise<{ answer: string, sources: Source[], tags: string[] }>}
 *
 * [실제 API 교체 시]
 * fetch 블록을 try 안에, mock 블록을 catch 안에 두거나
 * USE_MOCK 플래그로 분기하세요.
 */
export async function sendMessage({ channelId, message, history }) {
  // ── mock 응답 (API 미연결 상태)
  await delay(MOCK_DELAY);
  const { text, sources } = pickMockResponse(channelId);
  return {
    answer: text,
    sources,
    tags: [],
    suggestedChannelId: null,  // 백엔드 연결 시 채워짐 — 예: "visa" | "school" | null
  };

  /* ── fetch 교체 예시 (위 mock 삭제 후 아래 주석 해제) ──
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channelId, message, history }),
  });

  if (!res.ok) {
    const { text, sources } = pickMockResponse(channelId);
    return { answer: text, sources, tags: [], suggestedChannelId: null };
  }

  const data = await res.json();
  return {
    answer            : data.answer             ?? '',
    sources           : data.sources            ?? [],
    tags              : data.tags               ?? [],
    suggestedChannelId: data.suggestedChannelId ?? null,
  };
  */
}

/**
 * Message 객체 생성 헬퍼 (컴포넌트에서 직접 사용 가능)
 * re-export하여 import 경로를 한 곳으로 통일합니다.
 */
export { createMessage } from '../data/mockMessages';

// ── 내부 유틸 ─────────────────────────────────────────────────────────────

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
