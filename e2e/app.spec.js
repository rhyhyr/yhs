const { test, expect } = require('@playwright/test');

test('E2E 시나리오 1: 메인 페이지 및 헬스체크 정상 작동 확인', async ({ page }) => {
  // 1. 메인 페이지 접근 테스트
  const response = await page.goto('/');
  expect(response.status()).toBe(200);
  
  // 2. 헬스체크 API 테스트
  const healthResponse = await page.goto('/health');
  const body = await healthResponse.json();
  expect(body.status).toBe('ok');
});

test('E2E 시나리오 2: [스크린샷 캡처용] 의도된 실패 테스트', async ({ page }) => {
  // 일부러 존재하지 않는 페이지로 이동하여 에러를 유발합니다.
  const response = await page.goto('/this-page-does-not-exist');
  // 404가 나와야 하는데 200을 기대하므로 무조건 실패 -> Playwright가 자동 스크린샷 찰칵!
  expect(response.status()).toBe(200);
});