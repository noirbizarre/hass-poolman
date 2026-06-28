import { CARD_TAGS, cardLocator, expect, gotoCustomDashboard, test } from "./fixtures.js";

/**
 * Smoke tests: the custom-cards demo dashboard loads and every first-party
 * Pool Manager Lovelace card renders without throwing.
 */
test.describe("custom cards dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await gotoCustomDashboard(page);
  });

  test("renders the pool overview card with metrics", async ({ page }) => {
    const card = cardLocator(page, CARD_TAGS.overview);
    await expect(card).toBeVisible();
    await expect(card.locator(".header .title")).toBeVisible();
    await expect(card.locator(".badge")).toBeVisible();
    await expect(card.locator(".metric[data-key]").first()).toBeVisible();
  });

  test("renders the problem card", async ({ page }) => {
    await expect(cardLocator(page, CARD_TAGS.problem)).toBeVisible();
  });

  test("renders the recommendations card", async ({ page }) => {
    await expect(cardLocator(page, CARD_TAGS.recommendations)).toBeVisible();
  });

  test("renders the action history card with seeded actions", async ({ page }) => {
    const card = cardLocator(page, CARD_TAGS.actionHistory);
    await expect(card).toBeVisible();
    // The demo seeds at least one action via poolman.record_action.
    await expect(card.locator("ha-card")).toBeVisible();
  });

  test("renders the quick actions card with the analyze button", async ({ page }) => {
    const card = cardLocator(page, CARD_TAGS.quickActions);
    await expect(card).toBeVisible();
    await expect(card.locator('button.qa-btn[data-action="analyze"]')).toBeVisible();
  });

  test("loads without uncaught page errors", async ({ page, pageErrors }) => {
    // Touch every card so any lazy render path executes.
    for (const tag of Object.values(CARD_TAGS)) {
      await expect(cardLocator(page, tag)).toBeVisible();
    }
    expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  });
});
