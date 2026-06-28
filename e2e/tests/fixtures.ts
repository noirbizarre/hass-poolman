import { test as base, type Locator, type Page } from "@playwright/test";

/**
 * URL path of the demo dashboard that uses the first-party custom cards.
 */
export const CUSTOM_DASHBOARD = "/pool-custom/0";

/**
 * Custom element tags for the five first-party Pool Manager Lovelace cards.
 */
export const CARD_TAGS = {
  overview: "poolman-pool-overview-card",
  problem: "poolman-problem-card",
  recommendations: "poolman-recommendations-card",
  actionHistory: "poolman-action-history-card",
  quickActions: "poolman-quick-actions-card",
} as const;

/**
 * Return a locator for a custom card by its element tag. Playwright pierces
 * open shadow roots, so descendant selectors work across the Lit boundary.
 */
export function cardLocator(page: Page, tag: string): Locator {
  return page.locator(tag).first();
}

/** URL of the Pool Manager card bundle served by the integration. */
const CARD_BUNDLE_URL = "/poolman_frontend/poolman-cards.js";

/**
 * Navigate to the custom-cards dashboard and ensure the Pool Manager card
 * bundle has registered its custom elements.
 *
 * Home Assistant loads Lovelace module resources asynchronously, so a freshly
 * created storage-mode dashboard can render "configuration error" placeholders
 * if the view paints before the bundle finishes importing. Rather than relying
 * on fragile page reloads (which the SPA can abort mid-flight), this helper
 * deterministically imports the bundle in the page context when the overview
 * element is not yet defined, then forces the Lovelace view to re-render.
 */
export async function gotoCustomDashboard(page: Page): Promise<void> {
  await page.goto(CUSTOM_DASHBOARD, { waitUntil: "domcontentloaded" });
  await page.locator("home-assistant").waitFor({ state: "attached" });

  // Wait for the bundle's custom elements to be defined, importing the module
  // ourselves if HA has not finished loading the Lovelace resource yet.
  await page.waitForFunction(
    async (bundleUrl) => {
      if (customElements.get("poolman-pool-overview-card")) return true;
      try {
        await import(bundleUrl);
      } catch {
        return false;
      }
      return Boolean(customElements.get("poolman-pool-overview-card"));
    },
    CARD_BUNDLE_URL,
    { timeout: 30_000, polling: 1_000 },
  );

  // If the view painted error cards before the elements were defined, navigate
  // away and back so Lovelace re-renders the cards with the now-known elements.
  const overview = cardLocator(page, CARD_TAGS.overview);
  if (!(await overview.isVisible().catch(() => false))) {
    await page.goto("/lovelace/0", { waitUntil: "domcontentloaded" }).catch(() => undefined);
    await page.goto(CUSTOM_DASHBOARD, { waitUntil: "domcontentloaded" });
    await page.locator("home-assistant").waitFor({ state: "attached" });
  }

  await overview.waitFor({ state: "visible" });
}

/**
 * Test fixture that collects uncaught page errors so specs can assert the
 * dashboard rendered without throwing.
 */
export const test = base.extend<{ pageErrors: string[] }>({
  pageErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await use(errors);
  },
});

export { expect } from "@playwright/test";
