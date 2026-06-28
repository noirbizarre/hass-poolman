import { CARD_TAGS, cardLocator, expect, gotoCustomDashboard, test } from "./fixtures.js";

/**
 * Interactive flow: clicking "Analyze" on the Quick Actions card invokes the
 * `poolman.analyze` service and the button transitions through its pending and
 * success states.
 */
test.describe("quick actions", () => {
  test.beforeEach(async ({ page }) => {
    await gotoCustomDashboard(page);
    await cardLocator(page, CARD_TAGS.quickActions).waitFor({ state: "visible" });
  });

  test("analyze button reaches the success state", async ({ page, pageErrors }) => {
    const card = cardLocator(page, CARD_TAGS.quickActions);
    const analyze = card.locator('button.qa-btn[data-action="analyze"]');

    await expect(analyze).toBeVisible();
    await expect(analyze).toHaveAttribute("data-state", "idle");

    await analyze.click();

    // The button reflects its lifecycle via the `data-state` attribute and
    // settles on "success" (the success state resets to idle after ~1.5s, but
    // Playwright polls fast enough to observe it). The retrying assertion also
    // guards against a transient "error" state from a failed service call.
    await expect(analyze).toHaveAttribute("data-state", "success", { timeout: 10_000 });

    // No error message surfaced for the analyze action.
    await expect(card.locator('.qa-error-message[data-action="analyze"]')).toHaveCount(0);

    expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  });
});
