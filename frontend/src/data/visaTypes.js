/**
 * 비자 유형 선택지.
 * value 는 프로필(localStorage/API)에 저장되는 값이라 언어를 바꿔도 그대로 두고,
 * 화면에 보이는 이름만 i18n visaTypes.{key} 로 번역한다.
 */
export const VISA_OPTIONS = [
  { value: 'D-2 학생',     key: 'd2' },
  { value: 'D-4 어학연수', key: 'd4' },
  { value: 'F-2 거주',     key: 'f2' },
  { value: '기타',         key: 'other' },
];

/** 저장된 비자 유형 값 → 번역 키 (목록에 없는 자유 입력값이면 null) */
export function visaTypeKey(value) {
  return VISA_OPTIONS.find(o => o.value === value)?.key ?? null;
}
