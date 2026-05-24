import { describe, expect, it, beforeAll } from "vitest";

import "../poolman-pool-overview-card.js";
import type { HomeAssistant, PoolOverviewCardConfig } from "../types.js";
import { PoolmanPoolOverviewCard } from "../poolman-pool-overview-card.js";

function makeHass(states: Record<string, { state: string; attrs?: Record<string, unknown> }>): HomeAssistant {
  const hass: HomeAssistant = {
    states: {},
    entities: {},
    devices: {
      dev1: { id: "dev1", name: "Demo Pool", name_by_user: null },
    },
  };
  for (const [entity_id, value] of Object.entries(states)) {
    hass.states[entity_id] = {
      entity_id,
      state: value.state,
      attributes: value.attrs ?? {},
    };
    hass.entities![entity_id] = {
      entity_id,
      device_id: "dev1",
      unique_id: entity_id,
      platform: "poolman",
    };
  }
  return hass;
}

async function mount(card: PoolmanPoolOverviewCard): Promise<HTMLElement> {
  document.body.appendChild(card);
  await card.updateComplete;
  return card.shadowRoot!.querySelector("ha-card") as HTMLElement;
}

beforeAll(() => {
  // Stub ha-card so the card renders inside the test DOM.
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
    const card = new PoolmanPoolOverviewCard();
    expect(() => card.setConfig(undefined as unknown as PoolOverviewCardConfig)).toThrow();
  });

  it("rejects config without device_id or entities", () => {
    const card = new PoolmanPoolOverviewCard();
    expect(() => card.setConfig({ type: "custom:poolman-pool-overview-card" })).toThrow(
      /device_id/,
    );
  });

  it("accepts config with device_id", () => {
    const card = new PoolmanPoolOverviewCard();
    card.setConfig({
      type: "custom:poolman-pool-overview-card",
      device_id: "dev1",
    });
    expect(card.getCardSize()).toBe(3);
  });
});

describe("rendering", () => {
  it("renders metrics, status badge, score and recommendation count", async () => {
    const hass = makeHass({
      "sensor.demo_pool_status": { state: "warning" },
      "sensor.demo_pool_water_quality_score": { state: "72" },
      "sensor.demo_pool_recommendations": {
        state: "2",
        attrs: { recommendations: [{ id: "a" }, { id: "b" }] },
      },
      "sensor.demo_pool_temperature": {
        state: "26.0",
        attrs: { unit_of_measurement: "°C" },
      },
      "sensor.demo_pool_ph": { state: "7.8" },
      "sensor.demo_pool_free_chlorine": {
        state: "0.8",
        attrs: { unit_of_measurement: "mg/L" },
      },
    });

    const card = new PoolmanPoolOverviewCard();
    card.setConfig({ type: "custom:poolman-pool-overview-card", device_id: "dev1" });
    card.hass = hass;
    const root = await mount(card);
    const text = root.textContent ?? "";

    expect(text).toContain("Demo Pool");
    expect(text).toContain("WARNING");
    expect(text).toContain("26.0 °C");
    expect(text).toContain("7.8");
    expect(text).toContain("0.8 mg/L");
    expect(text).toContain("72 / 100");
    expect(text).toContain("2 recommendations");
  });

  it("renders MISSING placeholder for unavailable metrics", async () => {
    const hass = makeHass({
      "sensor.demo_pool_status": { state: "ok" },
      "sensor.demo_pool_water_quality_score": { state: "95" },
      "sensor.demo_pool_recommendations": { state: "0", attrs: { recommendations: [] } },
      "sensor.demo_pool_temperature": { state: "unavailable" },
      "sensor.demo_pool_ph": { state: "7.2" },
      "sensor.demo_pool_free_chlorine": { state: "unknown" },
    });

    const card = new PoolmanPoolOverviewCard();
    card.setConfig({ type: "custom:poolman-pool-overview-card", device_id: "dev1" });
    card.hass = hass;
    const root = await mount(card);
    const cells = Array.from(root.querySelectorAll(".metric"));
    const temp = cells.find((c) => c.getAttribute("data-key") === "temperature")!;
    const cl = cells.find((c) => c.getAttribute("data-key") === "free_chlorine")!;

    expect(temp.querySelector(".metric-value")!.textContent).toBe("—");
    expect(cl.querySelector(".metric-value")!.textContent).toBe("—");
    expect(root.textContent).toContain("Your pool is in good condition");
  });

  it("falls back to ORP when free_chlorine is unavailable", async () => {
    const hass = makeHass({
      "sensor.demo_pool_status": { state: "ok" },
      "sensor.demo_pool_temperature": { state: "26" },
      "sensor.demo_pool_ph": { state: "7.4" },
      "sensor.demo_pool_free_chlorine": { state: "unavailable" },
      "sensor.demo_pool_orp": { state: "720", attrs: { unit_of_measurement: "mV" } },
    });

    const card = new PoolmanPoolOverviewCard();
    card.setConfig({ type: "custom:poolman-pool-overview-card", device_id: "dev1" });
    card.hass = hass;
    const root = await mount(card);
    const keys = Array.from(root.querySelectorAll(".metric")).map((c) =>
      c.getAttribute("data-key"),
    );
    expect(keys).toEqual(["temperature", "ph", "orp"]);
    expect(root.textContent).toContain("720 mV");
  });

  it("recommendation row fires hass-more-info when no nav target", async () => {
    const hass = makeHass({
      "sensor.demo_pool_status": { state: "warning" },
      "sensor.demo_pool_recommendations": {
        state: "1",
        attrs: { recommendations: [{ id: "x" }] },
      },
      "sensor.demo_pool_temperature": { state: "26" },
      "sensor.demo_pool_ph": { state: "7.2" },
      "sensor.demo_pool_free_chlorine": { state: "1.0" },
    });

    const card = new PoolmanPoolOverviewCard();
    card.setConfig({ type: "custom:poolman-pool-overview-card", device_id: "dev1" });
    card.hass = hass;
    const root = await mount(card);

    let detail: { entityId: string } | undefined;
    card.addEventListener("hass-more-info", (ev: Event) => {
      detail = (ev as CustomEvent).detail;
    });
    (root.querySelector(".recommendations") as HTMLElement).click();
    expect(detail?.entityId).toBe("sensor.demo_pool_recommendations");
  });

  it("ignores per-parameter status sensors when resolving global status", async () => {
    const hass = makeHass({
      "sensor.demo_pool_status": { state: "critical" },
      "sensor.demo_pool_ph_status": { state: "high" },
      "sensor.demo_pool_temperature": { state: "26" },
      "sensor.demo_pool_ph": { state: "8.4" },
      "sensor.demo_pool_free_chlorine": { state: "0.4" },
    });

    const card = new PoolmanPoolOverviewCard();
    card.setConfig({ type: "custom:poolman-pool-overview-card", device_id: "dev1" });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("CRITICAL");
  });
});
