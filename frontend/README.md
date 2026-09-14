# YUHAK1 0403 수정사항
1. 프로젝트 파일 구조 리팩토링
pages/ hooks/ store/ api/ data/ styles/ components/ 폴더 구조로 재편

2. ChatScreen UX 개선
웰컴 카드 (첫 진입 안내 화면)
카테고리 단축 칩 4개 (비자, 취업, 학교, 주거)
채널 생성 확인 모달 시트

4. 채널 상태 크로스-스크린 공유
createdChannels 를 로컬 state → AppContext 전역으로 이동
ChatScreen에서 만든 채널이 HomeScreen에도 표시되게 연동

6. HomeScreen 구조 수정
하드코딩 채널 목록 제거
사용자 생성 채널만 표시
채널 없을 때 ghost 예시 카드 5개 표시

8. HomeScreen "지금 확인할 것" ghost 처리
URGENT_ITEMS 섹션 opacity: 0.38 적용
클릭 시 "이 항목은 예시입니다" 토스트

10. BridgeScreen 신규 추가
온보딩 완료 → 메인채팅 사이 중간 안내 화면
힌트 카드 3개, "메인채팅 시작" / "홈 먼저 보기" 버튼

12. 데이터 & API 레이어 구성
신규 파일	역할
data/channels.js	채널 메타 배열
data/mockMessages.js	채널별 mock 응답 풀 + createMessage()
api/chat.js	mock → fetch 교체 가능한 채팅 API 레이어
api/config.js	BASE_URL 환경변수

14. 채널별 전용 화면 추가
ChannelChatScreen.jsx — channelId props 받는 공통 컴포넌트
SchoolScreen, JobScreen, HouseScreen, InsuranceScreen — 각각 <ChannelChatScreen channelId="..." /> 래퍼

16. P0 하드코딩 → ghost + API 연결 준비
신규 API 파일 3개:

파일	함수
api/user.js	getMyProfile(), getVisaInfo(), getMyChannels(), createChannel()
api/steps.js	getVisaSteps(), updateStepStatus()
api/calendar.js	getCalendarEvents(year, month)
화면 수정:
ProfileScreen — API 연동 + 프로필/비자 카드 opacity: 0.55 + 예시 뱃지
VisaScreen — API 연동 + D-87 버튼·정보 패널 ghost
CalendarScreen — API 연동 + 이벤트 ghost, 시작 날짜 오늘로 변경
AppContext — getVisaSteps() 마운트 시 로드, toggleStep() 에서 updateStepStatus() 호출

10. 채널별 RAG 지원
api/chat.js
응답에 suggestedChannelId 필드 추가
hooks/useChatChannel.js

chatApi.js → chat.js 통합 (파일 1개로 통일)
suggestedChannelId 상태 관리 + clearSuggestion() 반환
ChatScreen.jsx

추천 채널 칩 펄스 강조 (.suggested CSS + 애니메이션)
추천 채널 카드 인라인 표시
goToChannel() 에서 메인채팅 대화를 initialHistory 로 전달
ChannelChatScreen.jsx

navParams.initialHistory 수신 → 채널 API 호출 시 history에 프리픽스
globalStyles.js

.main-shortcut-chip.suggested 펄스 애니메이션
.suggestion-card 스타일
api/chatApi.js → 삭제 (통합 완료)
