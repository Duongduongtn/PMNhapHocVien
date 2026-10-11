import { defineConfig } from "@playwright/test";

// E2E giả backend (page.route) — KHÔNG đụng DB thật. File *.e2e.ts để vitest không nhặt nhầm.
export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.e2e.ts",
  timeout: 60_000,
  reporter: "list",
  use: { baseURL: "http://localhost:3011", viewport: { width: 1280, height: 800 } },
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3011",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
