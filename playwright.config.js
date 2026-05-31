const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  // 실패했을 때만 스크린샷을 찍도록 자동 설정
  use: {
    baseURL: 'http://127.0.0.1:8080',
    screenshot: 'only-on-failure',
  },
  // 테스트를 돌리기 전에 우리 서버(index.js)를 백그라운드에서 자동으로 켭니다.
  webServer: {
    command: 'node index.js',
    url: 'http://127.0.0.1:8080/health',
    reuseExistingServer: !process.env.CI,
  },
});