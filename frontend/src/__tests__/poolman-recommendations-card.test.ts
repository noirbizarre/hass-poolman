import { beforeAll, describe, expect, it, vi } from "vitest";

import "../poolman-recommendations-card.js";
import { PoolmanRecommendationsCard } from "../poolman-recommendations-card.js";
import type {
  HomeAssistant,
  PoolRecommendationsCardConfig,
  RecommendationDTO,
} from "../types.js";

interface FakeEntity {
  state: string;
  attrs?: Record<string, unknown>;
}

function makeHass(
  states: Record<string, FakeEntity>,
  overrides: Partial<HomeAssistant> = {},
): HomeAssistant {
  const hass: HomeAssistant = {
    states: {},
    entities: {},
    devices: {
      dev1: { id: "dev1", name: "Demo Pool", name_by_user: null },
    },
    locale: { language: "en" },
    ...overrides,
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

async function mount(card: PoolmanRecommendationsCard): Promise<HTMLElement> {
  document.body.appendChild(card);
  await card.updateComplete;
  return card.shadowRoot!.querySelector("ha-card") as HTMLElement;
}

function recs(...items: Partial<RecommendationDTO>[]): RecommendationDTO[] {
  return items.map((item, i) => ({
    id: item.id ?? `rec_${i}`,
    type: item.type ?? "chemistry",
    severity: item.severity ?? "medium",
    priority: item.priority,
    title: item.title ?? `Recommendation ${i}`,
    description: item.description,
    reason: item.reason,
    treatments: item.treatments,
    related_metrics: item.related_metrics,
  }));
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
    const card = new PoolmanRecommendationsCard();
    expect(() =>
      card.setConfig(undefined as unknown as PoolRecommendationsCardConfig),
    ).toThrow();
  });

  it("rejects config without device_id or entity", () => {
    const card = new PoolmanRecommendationsCard();
    expect(() =>
      card.setConfig({ type: "custom:poolman-recommendations-card" }),
    ).toThrow(/device_id/);
  });

  it("accepts device_id-only config", () => {
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    expect(card.getCardSize()).toBeGreaterThan(0);
  });

  it("accepts explicit entity override", () => {
    const card = new PoolmanRecommendationsCard();
    expect(() =>
      card.setConfig({
        type: "custom:poolman-recommendations-card",
        entity: "sensor.foo_recommendations",
      }),
    ).not.toThrow();
  });
});

describe("rendering", () => {
  it("renders one row per recommendation with priority label", async () => {
    const hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "2",
        attrs: {
          recommendations: recs(
            { id: "rec_a", title: "Lower pH", priority: "high" },
            { id: "rec_b", title: "Boost filtration", priority: "low" },
          ),
        },
      },
    });

    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    const rows = Array.from(root.querySelectorAll(".rec"));
    expect(rows).toHaveLength(2);
    expect(rows[0].getAttribute("data-priority")).toBe("high");
    expect(rows[0].textContent).toContain("Lower pH");
    expect(rows[0].textContent).toContain("HIGH");
    expect(rows[1].textContent).toContain("Boost filtration");
    expect(rows[1].textContent).toContain("LOW");
  });

  it("renders the empty state when count is zero", async () => {
    const hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "0",
        attrs: { recommendations: [] },
      },
    });

    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.querySelector(".empty")?.textContent).toContain(
      "Your pool is in good condition",
    );
    expect(root.querySelectorAll(".rec")).toHaveLength(0);
  });

  it("falls back to severity when priority is missing", async () => {
    const hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "1",
        attrs: {
          recommendations: recs({ severity: "critical", title: "Hazard" }),
        },
      },
    });
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.querySelector(".rec")?.getAttribute("data-priority")).toBe(
      "critical",
    );
  });

  it("renders the unavailable state when the entity is missing", async () => {
    const hass = makeHass({});
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.querySelector(".unavailable")?.textContent).toContain(
      "Recommendations unavailable",
    );
  });

  it("expands a row to show reason and treatments", async () => {
    const hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "1",
        attrs: {
          recommendations: recs({
            id: "rec_a",
            title: "Lower pH",
            priority: "medium",
            reason: "ph_too_high",
            treatments: [
              {
                product_id: "ph_minus",
                name: "pH-",
                quantity: 300,
                unit: "g",
              },
            ],
            related_metrics: ["ph"],
          }),
        },
      },
    });
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector(".rec-head") as HTMLElement).click();
    await card.updateComplete;
    const detail = root.querySelector(".rec-detail")!;
    expect(detail.textContent).toContain("ph_too_high");
    expect(detail.textContent).toContain("pH-");
    expect(detail.textContent).toMatch(/300\s*g/);
    expect(detail.querySelector(".metric-chip")?.textContent).toBe("ph");
  });
});

describe("ignore", () => {
  it("removes the row without calling the service", async () => {
    const callService = vi.fn();
    const hass = makeHass(
      {
        "sensor.demo_pool_recommendations": {
          state: "1",
          attrs: { recommendations: recs({ id: "rec_a", title: "Foo" }) },
        },
      },
      { callService },
    );
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.ignore") as HTMLButtonElement).click();
    await card.updateComplete;
    expect(root.querySelectorAll(".rec")).toHaveLength(0);
    expect(root.querySelector(".empty")).toBeTruthy();
    expect(callService).not.toHaveBeenCalled();
  });

  it("re-emitted recommendation id is no longer suppressed", async () => {
    const hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "1",
        attrs: { recommendations: recs({ id: "rec_a", title: "Foo" }) },
      },
    });
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.ignore") as HTMLButtonElement).click();
    await card.updateComplete;
    expect(root.querySelectorAll(".rec")).toHaveLength(0);

    // Backend drops the recommendation entirely (count -> 0).
    card.hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "0",
        attrs: { recommendations: [] },
      },
    });
    await card.updateComplete;

    // Then re-emits the same id later.
    card.hass = makeHass({
      "sensor.demo_pool_recommendations": {
        state: "1",
        attrs: { recommendations: recs({ id: "rec_a", title: "Foo" }) },
      },
    });
    await card.updateComplete;
    await card.updateComplete;
    const rows = card.shadowRoot!.querySelectorAll(".rec");
    expect(rows).toHaveLength(1);
  });
});

describe("apply", () => {
  it("calls the apply_recommendation service without confirming for medium priority", async () => {
    const callService = vi.fn().mockResolvedValue(undefined);
    const hass = makeHass(
      {
        "sensor.demo_pool_recommendations": {
          state: "1",
          attrs: {
            recommendations: recs({
              id: "rec_med",
              title: "Lower pH",
              priority: "medium",
            }),
          },
        },
      },
      { callService },
    );
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.apply") as HTMLButtonElement).click();
    // Allow the async _apply chain to settle.
    await Promise.resolve();
    await Promise.resolve();
    expect(callService).toHaveBeenCalledWith("poolman", "apply_recommendation", {
      device_id: "dev1",
      recommendation_id: "rec_med",
    });
  });

  it("prompts before applying a critical recommendation", async () => {
    const callService = vi.fn().mockResolvedValue(undefined);
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const hass = makeHass(
      {
        "sensor.demo_pool_recommendations": {
          state: "1",
          attrs: {
            recommendations: recs({
              id: "rec_crit",
              title: "Shock pool",
              priority: "critical",
            }),
          },
        },
      },
      { callService },
    );
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.apply") as HTMLButtonElement).click();
    await Promise.resolve();
    await Promise.resolve();
    expect(confirmSpy).toHaveBeenCalled();
    expect(callService).toHaveBeenCalledTimes(1);
    confirmSpy.mockRestore();
  });

  it("does not call the service when the user cancels the prompt", async () => {
    const callService = vi.fn().mockResolvedValue(undefined);
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    const hass = makeHass(
      {
        "sensor.demo_pool_recommendations": {
          state: "1",
          attrs: {
            recommendations: recs({
              id: "rec_crit",
              title: "Shock pool",
              priority: "critical",
            }),
          },
        },
      },
      { callService },
    );
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.apply") as HTMLButtonElement).click();
    await Promise.resolve();
    await Promise.resolve();
    expect(confirmSpy).toHaveBeenCalled();
    expect(callService).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it("never prompts when confirm_apply is `never`", async () => {
    const callService = vi.fn().mockResolvedValue(undefined);
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const hass = makeHass(
      {
        "sensor.demo_pool_recommendations": {
          state: "1",
          attrs: {
            recommendations: recs({
              id: "rec_crit",
              title: "Shock pool",
              priority: "critical",
            }),
          },
        },
      },
      { callService },
    );
    const card = new PoolmanRecommendationsCard();
    card.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
      confirm_apply: "never",
    });
    card.hass = hass;
    const root = await mount(card);
    (root.querySelector("button.apply") as HTMLButtonElement).click();
    await Promise.resolve();
    await Promise.resolve();
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(callService).toHaveBeenCalledTimes(1);
    confirmSpy.mockRestore();
  });
});
