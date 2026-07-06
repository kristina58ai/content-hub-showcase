import { defineConfig } from "@playwright/test";

// E2E smoke of the recruiter flow (§B.5.14). Dev servers are started
// externally before running:
//   backend : uvicorn on :8000 (LLM_PRIMARY_PROVIDER=fake, redis up)
//   frontend: next dev on :3000
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  retries: 0,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    screenshot: "only-on-failure",
  },
});
