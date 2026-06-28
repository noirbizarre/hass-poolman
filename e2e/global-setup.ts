import { request, type FullConfig } from "@playwright/test";
import { writeFileSync } from "node:fs";

/**
 * Global setup: wait for the demo stack to finish seeding, then authenticate
 * once and persist the browser session to `storage-state.json`.
 *
 * The docker-compose `setup` service onboards the `admin` user and creates the
 * `pool-custom` / `pool-builtin` dashboards. We consider the instance ready
 * when onboarding is complete and the Pool Manager card bundle is served,
 * which means the integration loaded.
 */

const HA_URL = process.env.HA_URL ?? "http://localhost:8123";
const USERNAME = process.env.HA_USERNAME ?? "admin";
const PASSWORD = process.env.HA_PASSWORD ?? "admin";
const STORAGE_STATE = "storage-state.json";

const READY_TIMEOUT_MS = 180_000;
const POLL_INTERVAL_MS = 3_000;
const CARD_BUNDLE_PATH = "/poolman_frontend/poolman-cards.js";

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Poll Home Assistant until onboarding is done and the Pool Manager card
 * bundle is served. Throws if the deadline is exceeded.
 */
async function waitForSeededInstance(): Promise<void> {
  const ctx = await request.newContext({ baseURL: HA_URL });
  const deadline = Date.now() + READY_TIMEOUT_MS;
  let lastError = "unknown";

  try {
    while (Date.now() < deadline) {
      try {
        // Onboarding complete -> either the endpoint is unregistered (404,
        // older HA) or it returns 200 with every step marked done.
        const onboarding = await ctx.get("/api/onboarding");
        let onboardingDone = onboarding.status() === 404;
        if (onboarding.ok()) {
          const steps = (await onboarding.json()) as Array<{ done: boolean }>;
          onboardingDone = steps.length > 0 && steps.every((s) => s.done);
        }

        // The integration registers the card bundle as a static path.
        const bundle = await ctx.get(CARD_BUNDLE_PATH);
        const bundleServed = bundle.ok();

        if (onboardingDone && bundleServed) {
          return;
        }
        lastError = `onboardingDone=${onboardingDone} bundleServed=${bundleServed}`;
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
      }
      await sleep(POLL_INTERVAL_MS);
    }
  } finally {
    await ctx.dispose();
  }

  throw new Error(
    `Home Assistant demo did not finish seeding within ${READY_TIMEOUT_MS}ms (last: ${lastError})`,
  );
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token: string;
  expires_in: number;
  ha_auth_provider?: string;
}

/**
 * Authenticate against Home Assistant via its auth HTTP API, mirroring the
 * demo `setup.py` login flow. Returns the token payload.
 *
 * Driving the auth REST API directly (rather than the login UI) is robust
 * against the deeply nested shadow-DOM login form rendered by `ha-authorize`.
 */
async function authenticate(): Promise<TokenResponse> {
  const clientId = `${HA_URL}/`;
  const ctx = await request.newContext({ baseURL: HA_URL });

  try {
    const flowResp = await ctx.post("/auth/login_flow", {
      data: {
        client_id: clientId,
        handler: ["homeassistant", null],
        redirect_uri: clientId,
      },
    });
    const flow = (await flowResp.json()) as { flow_id: string };

    const loginResp = await ctx.post(`/auth/login_flow/${flow.flow_id}`, {
      data: { client_id: clientId, username: USERNAME, password: PASSWORD },
    });
    const login = (await loginResp.json()) as { type?: string; result?: string };
    if (login.type !== "create_entry" || !login.result) {
      throw new Error(`Home Assistant login failed: ${JSON.stringify(login)}`);
    }

    const tokenResp = await ctx.post("/auth/token", {
      form: {
        client_id: clientId,
        grant_type: "authorization_code",
        code: login.result,
      },
    });
    return (await tokenResp.json()) as TokenResponse;
  } finally {
    await ctx.dispose();
  }
}

/**
 * Authenticate and persist a Playwright storage state seeding the
 * `hassTokens` localStorage entry the Home Assistant frontend reads on load.
 */
async function captureStorageState(): Promise<void> {
  const token = await authenticate();
  const clientId = `${HA_URL}/`;

  // Shape expected by the HA frontend (`saveTokens` in home-assistant-js-websocket).
  const hassTokens = {
    access_token: token.access_token,
    token_type: token.token_type,
    refresh_token: token.refresh_token,
    expires_in: token.expires_in,
    ha_auth_provider: token.ha_auth_provider,
    hassUrl: HA_URL,
    clientId,
    expires: Date.now() + token.expires_in * 1000,
  };

  const storageState = {
    cookies: [],
    origins: [
      {
        origin: HA_URL,
        localStorage: [
          { name: "hassTokens", value: JSON.stringify(hassTokens) },
        ],
      },
    ],
  };

  writeFileSync(STORAGE_STATE, JSON.stringify(storageState, null, 2));
}

export default async function globalSetup(_config: FullConfig): Promise<void> {
  await waitForSeededInstance();
  await captureStorageState();
}
