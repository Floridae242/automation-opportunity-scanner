import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
  webServer: [
    {
      command: "apps/api/.venv/bin/uvicorn aos_api.main:create_app --factory --host 127.0.0.1 --port 8100",
      url: "http://127.0.0.1:8100/health/live",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "npm run start --workspace apps/web -- --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      env: { API_BASE_URL: "http://127.0.0.1:8100" },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
