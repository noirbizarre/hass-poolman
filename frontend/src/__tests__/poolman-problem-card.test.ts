import { describe, expect, it, beforeAll } from "vitest";

import "../poolman-problem-card.js";
import type {
  HomeAssistant,
  PoolProblemCardConfig,
  ProblemDTO,
} from "../types.js";
import { PoolmanProblemCard } from "../poolman-problem-card.js";

interface EntityFixture {
  state: string;
  attrs?: Record<string, unknown>;
}

function makeHass(states: Record<string, EntityFixture>): HomeAssistant {
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

async function mount(card: PoolmanProblemCard): Promise<HTMLElement> {
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
    const card = new PoolmanProblemCard();
    expect(() =>
      card.setConfig(undefined as unknown as PoolProblemCardConfig),
    ).toThrow();
  });

  it("rejects config without device_id or entity", () => {
    const card = new PoolmanProblemCard();
    expect(() =>
      card.setConfig({ type: "custom:poolman-problem-card" }),
    ).toThrow(/device_id/);
  });

  it("rejects non-positive max", () => {
    const card = new PoolmanProblemCard();
    expect(() =>
      card.setConfig({
        type: "custom:poolman-problem-card",
        device_id: "dev1",
        max: 0,
      }),
    ).toThrow(/max/);
  });

  it("accepts config with device_id", () => {
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    expect(card.getCardSize()).toBe(1);
  });

  it("exposes a stub config", () => {
    expect(PoolmanProblemCard.getStubConfig()).toEqual({
      type: "custom:poolman-problem-card",
    });
  });
});

describe("rendering", () => {
  function problem(overrides: Partial<ProblemDTO>): ProblemDTO {
    return {
      code: "test_code",
      severity: "medium",
      metric: null,
      value: null,
      expected_range: null,
      message: "Test message",
      ...overrides,
    };
  }

  it("renders empty state when count is 0", async () => {
    const hass = makeHass({
      "sensor.demo_pool_problems": {
        state: "0",
        attrs: { problems: [], worst_severity: "ok" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain(
      "No problems detected — pool is healthy",
    );
    expect(root.textContent).toContain("OK");
    expect(root.querySelector(".problem")).toBeNull();
  });

  it("renders problems preserving sensor order and severity colors", async () => {
    const problems: ProblemDTO[] = [
      problem({
        code: "ph_too_high",
        severity: "critical",
        metric: "ph",
        value: 7.9,
        expected_range: [7.2, 7.6],
        message: "pH is too high",
      }),
      problem({
        code: "chlorine_too_low",
        severity: "medium",
        metric: "chlorine",
        value: 0.3,
        expected_range: [1.0, 3.0],
        message: "Chlorine is too low",
      }),
      problem({
        code: "cya_low",
        severity: "low",
        metric: "cya",
        value: 20,
        expected_range: [30, 50],
        message: "CYA is a bit low",
      }),
    ];
    const hass = makeHass({
      "sensor.demo_pool_problems": {
        state: "3",
        attrs: { problems, worst_severity: "critical" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);

    const rows = Array.from(root.querySelectorAll(".problem"));
    expect(rows.map((r) => r.getAttribute("data-code"))).toEqual([
      "ph_too_high",
      "chlorine_too_low",
      "cya_low",
    ]);
    expect(rows.map((r) => r.getAttribute("data-severity"))).toEqual([
      "critical",
      "medium",
      "low",
    ]);

    const text = root.textContent ?? "";
    // pH formatting (2 decimals, no unit)
    expect(text).toContain("7.90");
    expect(text).toContain("7.20–7.60");
    // Chlorine formatting (1 decimal, mg/L)
    expect(text).toContain("0.3 mg/L");
    expect(text).toContain("1.0–3.0 mg/L");
    // CYA formatting (0 decimals, mg/L)
    expect(text).toContain("20 mg/L");
    expect(text).toContain("30–50 mg/L");

    // Severity badges
    expect(text).toContain("CRITICAL");
    expect(text).toContain("WARNING");
    expect(text).toContain("INFO");
  });

  it("falls back to message-only when metric or range is null", async () => {
    const problems: ProblemDTO[] = [
      problem({
        code: "freeform",
        severity: "medium",
        message: "Something is off",
      }),
    ];
    const hass = makeHass({
      "sensor.demo_pool_problems": {
        state: "1",
        attrs: { problems, worst_severity: "medium" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.querySelector(".details")).toBeNull();
    expect(root.textContent).toContain("Something is off");
  });

  it("renders the unavailable hint when the problems entity is unknown", async () => {
    const hass = makeHass({
      "sensor.demo_pool_problems": { state: "unavailable" },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("Problems entity unavailable");
  });

  it("renders the unavailable hint when no problems entity is found", async () => {
    const hass = makeHass({});
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("Problems entity unavailable");
  });

  it("respects `max` and surfaces a '+N more' hint", async () => {
    const problems: ProblemDTO[] = [
      problem({ code: "a", severity: "critical", message: "A" }),
      problem({ code: "b", severity: "medium", message: "B" }),
      problem({ code: "c", severity: "low", message: "C" }),
    ];
    const hass = makeHass({
      "sensor.demo_pool_problems": {
        state: "3",
        attrs: { problems, worst_severity: "critical" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
      max: 2,
    });
    card.hass = hass;
    const root = await mount(card);
    const rows = Array.from(root.querySelectorAll(".problem"));
    expect(rows.length).toBe(2);
    expect(root.textContent).toContain("+1 more problem");
  });

  it("accepts an explicit entity override", async () => {
    const problems: ProblemDTO[] = [
      problem({ code: "x", severity: "low", message: "Minor issue" }),
    ];
    const hass = makeHass({
      "sensor.custom_problems": {
        state: "1",
        attrs: { problems, worst_severity: "low" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      entity: "sensor.custom_problems",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("Minor issue");
    expect(root.textContent).toContain("INFO");
  });

  it("uses the configured name in the header", async () => {
    const hass = makeHass({
      "sensor.demo_pool_problems": {
        state: "0",
        attrs: { problems: [], worst_severity: "ok" },
      },
    });
    const card = new PoolmanProblemCard();
    card.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
      name: "Backyard Pool",
    });
    card.hass = hass;
    const root = await mount(card);
    expect(root.textContent).toContain("Backyard Pool");
  });
});
