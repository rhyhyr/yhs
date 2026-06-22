// Week12 (선택) - Playwright E2E 스모크 테스트
const { test, expect } = require("@playwright/test");

test("홈페이지 로드 및 기본 요소 확인", async ({ page }) => {
  await page.goto("https://taeing25.github.io/yhs_t/");

  // 타이틀 확인
  await expect(page).toHaveTitle(/Visa Navigator/);

  // 서비스 상태 배지 확인
  await expect(page.locator(".status-badge")).toBeVisible();
  await expect(page.locator(".status-badge")).toContainText("서비스 운영 중");

  // 핵심 기능 섹션 확인
  await expect(page.locator("h2").first()).toBeVisible();
});
