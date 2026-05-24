import { describe, expect, it, beforeAll } from "vitest";

import "../poolman-action-history-card.js";
import type {
  ActionDTO,
  ActionHistoryCardConfig,
  HomeAssistant,
} from "../types.js";
import { PoolmanActionHistoryCard } from "../poolman-action-history-card.js";

function makeHass(actions: Partial<ActionDTO>[]): HomeAssistant {
  const fullActions = actions.map((a, i) => ({
    id: `act_${i}`,
    type: "chemical",
    source: "user",
    treatment_id: "ph_minus_300g",
    quantity: 150,
    unit: "g",
    timestamp: new Date().toISOString(),
    recommendation_id: null,
    product_id: null,
    duration: null,
    ...a,
  })) as ActionDTO[];
  const hass: HomeAssistant = {
    states: {
      "sensor.demo_pool_action_history": {
        entity_id: "sensor.demo_pool_action_history",
        state: fullActions[0]?.timestamp ?? "unknown",
        attributes: {
          actions: fullActions,
          limit: 50,
          total: fullActions.length,
        },
      },
    },
    entities: {
      "sensor.demo_pool_action_history": {
        entity_id: "sensor.demo_pool_action_history",
        device_id: "dev1",
        unique_id: "demo_pool_action_history",
        platform: "poolman",
      },
    },
    devices: {
      dev1: { id: "dev1", name: "Demo Pool", name_by_user: null },
    },
    locale: { language: "en" },
  };
  return hass;
}

async function mount(card: PoolmanActionHistoryCard): Promise<HTMLElement> {
  document.body.appendChild(card);
  await card.updateComplete;
  return card.shadowRoot!.querySelector("ha-card") as HTMLElement;
}

beforeAll(() => {
  if (!customElements.get("ha-card")) {
    customElements.define(
      "ha-card",
      class extends HTMLElement {
        constructor() {
          super();
          this.attachShadow({ mode: "open" }).innerHTML = "<slot></slot>";
        }
      },
    );
  }
});

describe("setConfig", () => {
  it("rejects empty config", () => {
    const card = new PoolmanActionHistoryCard();
    expect(() =>
      card.setConfig(undefined as unknown as ActionHistoryCardConfig),
    ).toThrow();
  });

  it("rejects config without device_id or entities", () => {
    const card = new PoolmanActionHistoryCard();
    expect(() =>
      card.setConfig({ type: "custom:poolman-action-history-card" }),
    ).toThrow(/device_id/);
  });

  it("accepts config with device_id and clamps limit to 50", () => {
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
      limit: 9999,
    });
    expect(card.getCardSize()).toBe(4);
  });
});

describe("rendering", () => {
  it("shows the empty state when no actions are recorded", async () => {
    const hass = makeHass([]);
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("No actions recorded yet");
    expect(root.querySelector(".action-row")).toBeNull();
  });

  it("renders actions in reverse chronological order with icon, quantity and source badge", async () => {
    const today = new Date();
    const earlier = new Date(today.getTime() - 3600 * 1000 * 24);
    const hass = makeHass([
      {
        id: "old",
        type: "cleaning",
        source: "user",
        quantity: 0,
        unit: "",
        timestamp: earlier.toISOString(),
      },
      {
        id: "new",
        type: "chemical",
        source: "recommendation",
        recommendation_id: "rec_42",
        quantity: 150,
        unit: "g",
        timestamp: today.toISOString(),
      },
    ]);
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);

    const rows = Array.from(root.querySelectorAll(".action-row"));
    expect(rows.length).toBe(2);
    expect(rows[0].getAttribute("data-type")).toBe("chemical");
    expect(rows[0].textContent).toContain("🧪");
    expect(rows[0].textContent).toContain("150 g");
    expect(rows[0].querySelector(".source-badge.recommendation")).not.toBeNull();

    expect(rows[1].getAttribute("data-type")).toBe("cleaning");
    expect(rows[1].textContent).toContain("🧹");
    // Non-chemical actions show MISSING for quantity
    expect(rows[1].querySelector(".quantity")!.textContent).toBe("—");
  });

  it("groups rows under day headers (Today / Yesterday)", async () => {
    const today = new Date();
    const yesterday = new Date(today.getTime() - 3600 * 1000 * 24);
    const hass = makeHass([
      { id: "today", timestamp: today.toISOString() },
      { id: "yest", timestamp: yesterday.toISOString() },
    ]);
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    const headers = Array.from(root.querySelectorAll(".day-header")).map(
      (h) => h.textContent,
    );
    expect(headers).toEqual(["Today", "Yesterday"]);
  });

  it("honours the limit configuration", async () => {
    const now = Date.now();
    const hass = makeHass(
      Array.from({ length: 10 }, (_, i) => ({
        id: `a${i}`,
        timestamp: new Date(now - i * 3600 * 1000).toISOString(),
      })),
    );
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
      limit: 3,
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.querySelectorAll(".action-row").length).toBe(3);
  });

  it("dispatches hass-more-info when tapping an action linked to a recommendation", async () => {
    const hass = makeHass([
      {
        id: "rec_action",
        type: "chemical",
        source: "recommendation",
        recommendation_id: "rec_42",
        quantity: 150,
        unit: "g",
        timestamp: new Date().toISOString(),
      },
    ]);
    const card = new PoolmanActionHistoryCard();
    card.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);

    let detail: { entityId: string } | undefined;
    card.addEventListener("hass-more-info", (ev: Event) => {
      detail = (ev as CustomEvent).detail;
    });
    (root.querySelector(".action-row.interactive") as HTMLElement).click();
    expect(detail?.entityId).toBe("sensor.demo_pool_action_history");
  });
});
