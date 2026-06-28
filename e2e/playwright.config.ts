import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for the Pool Manager end-to-end suite.
 *
 * Tests run against the docker-compose demo Home Assistant instance
 * (see ../docker-compose.yaml). Locally, the `webServer` block boots the
 * stack on demand; in CI the stack is started by the workflow and reused.
 *
 * Authentication is performed once in `global-setup.ts`, which persists the
 * session to `storage-state.json` so individual specs skip the HA login UI.
 */

const HA_URL = process.env.HA_URL ?? "http://localhost:8123";

export default defineConfig({
  testDir: "./tests",
  outputDir: "test-results",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  globalSetup: "./global-setup.ts",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: HA_URL,
    storageState: "storage-state.json",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // Start the demo stack from the repository root. `--wait` blocks on the
    // homeassistant healthcheck; `global-setup.ts` additionally polls for the
    // seeded dashboards/bundle before authenticating.
    //
    // Always reuse an already-running instance: locally this avoids tearing
    // down a hand-started stack, and in CI the workflow starts the stack
    // before invoking the tests (idempotent `docker compose up -d --wait`).
    command: "docker compose up -d --wait",
    cwd: "..",
    url: HA_URL,
    timeout: 240_000,
    reuseExistingServer: true,
    stdout: "pipe",
    stderr: "pipe",
  },
});
