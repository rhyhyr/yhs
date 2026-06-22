/**
 * visa-navigator-utils
 * 비자 상태 포맷팅 등 간단한 유틸리티 함수 모음
 */

function formatVisaStatus(status) {
  return `[Visa Status] ${status.toUpperCase()}`;
}

function isValidStudentId(id) {
  return typeof id === "string" && id.length >= 4;
}

module.exports = { formatVisaStatus, isValidStudentId };

// 직접 실행 시 동작 확인
if (require.main === module) {
  console.log(formatVisaStatus("approved"));       // [Visa Status] APPROVED
  console.log(isValidStudentId("2024001"));        // true
}
