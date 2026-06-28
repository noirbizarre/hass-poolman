import { describe, expect, it } from "vitest";

import { firstPoolmanDeviceId } from "../editor/base.js";
import "../poolman-pool-overview-card.js";
import "../poolman-problem-card.js";
import "../poolman-recommendations-card.js";
import "../poolman-action-history-card.js";
import "../poolman-quick-actions-card.js";
import { PoolmanPoolOverviewCard } from "../poolman-pool-overview-card.js";
import { PoolmanProblemCard } from "../poolman-problem-card.js";
import { PoolmanRecommendationsCard } from "../poolman-recommendations-card.js";
import { PoolmanActionHistoryCard } from "../poolman-action-history-card.js";
import { PoolmanQuickActionsCard } from "../poolman-quick-actions-card.js";

describe("firstPoolmanDeviceId", () => {
  it("returns undefined when no devices are exposed", () => {
    expect(firstPoolmanDeviceId(undefined)).toBeUndefined();
    expect(firstPoolmanDeviceId({})).toBeUndefined();
  });

  it("prefers a device backed by a poolman entity", () => {
    const id = firstPoolmanDeviceId({
      devices: {
        dev1: { id: "dev1" },
        dev2: { id: "dev2" },
      },
      entities: {
        "sensor.other": { device_id: "dev1", platform: "demo" },
        "sensor.pool": { device_id: "dev2", platform: "poolman" },
      },
    });
    expect(id).toBe("dev2");
  });

  it("falls back to the first device when entities are unavailable", () => {
    const id = firstPoolmanDeviceId({
      devices: {
        dev1: { id: "dev1" },
      },
    });
    expect(id).toBe("dev1");
  });
});

describe("getConfigElement", () => {
  it.each([
    ["PoolmanPoolOverviewCard", PoolmanPoolOverviewCard, "poolman-pool-overview-card-editor"],
    ["PoolmanProblemCard", PoolmanProblemCard, "poolman-problem-card-editor"],
    [
      "PoolmanRecommendationsCard",
      PoolmanRecommendationsCard,
      "poolman-recommendations-card-editor",
    ],
    [
      "PoolmanActionHistoryCard",
      PoolmanActionHistoryCard,
      "poolman-action-history-card-editor",
    ],
    [
      "PoolmanQuickActionsCard",
      PoolmanQuickActionsCard,
      "poolman-quick-actions-card-editor",
    ],
  ])("%s exposes its editor element", async (_name, klass, tag) => {
    const element = await (
      klass as unknown as { getConfigElement: () => Promise<HTMLElement> }
    ).getConfigElement();
    expect(element.tagName.toLowerCase()).toBe(tag);
  });
});
