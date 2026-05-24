import { describe, expect, it, beforeAll, vi } from "vitest";

import "../poolman-quick-actions-card.js";
import { PoolmanQuickActionsCard } from "../poolman-quick-actions-card.js";
import type { HomeAssistant, QuickActionsCardConfig } from "../types.js";

interface ServiceCall {
  domain: string;
  service: string;
  data: Record<string, unknown> | undefined;
}

function makeHass(
  callService?: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ) => Promise<unknown>,
  language = "en",
): HomeAssistant {
  return {
    states: {},
    entities: {},
    devices: {
      dev1: { id: "dev1", name: "Demo Pool", name_by_user: null },
    },
    callService,
    locale: { language },
  };
}

async function mount(card: PoolmanQuickActionsCard): Promise<ShadowRoot> {
  document.body.appendChild(card);
  await card.updateComplete;
  return card.shadowRoot!;
}

function getButton(root: ShadowRoot, action: string): HTMLButtonElement {
  const btn = root.querySelector<HTMLButtonElement>(
    `button[data-action="${action}"]`,
  );
  if (!btn) throw new Error(`No button for action="${action}"`);
  return btn;
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
  it("rejects an empty config", () => {
    const card = new PoolmanQuickActionsCard();
    expect(() => card.setConfig(undefined as unknown as QuickActionsCardConfig)).toThrow();
  });

  it("rejects a config without device_id", () => {
    const card = new PoolmanQuickActionsCard();
    expect(() =>
      card.setConfig({ type: "custom:poolman-quick-actions-card" }),
    ).toThrow(/device_id/);
  });

  it("accepts a config with device_id", () => {
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    expect(card.getCardSize()).toBe(2);
  });
});

describe("rendering", () => {
  it("renders all default buttons", async () => {
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    card.hass = makeHass(vi.fn().mockResolvedValue(undefined));
    const root = await mount(card);

    expect(getButton(root, "analyze")).toBeTruthy();
    expect(getButton(root, "boost_2h")).toBeTruthy();
    expect(getButton(root, "boost_4h")).toBeTruthy();
    expect(getButton(root, "record")).toBeTruthy();
    expect(root.textContent).toContain("Demo Pool");
    expect(root.textContent).toContain("Analyze now");
  });

  it("hides buttons disabled via config", async () => {
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
      analyze: false,
      boost: false,
    });
    card.hass = makeHass(vi.fn().mockResolvedValue(undefined));
    const root = await mount(card);

    expect(
      root.querySelector("button[data-action=\"analyze\"]"),
    ).toBeNull();
    expect(
      root.querySelector("button[data-action=\"boost_2h\"]"),
    ).toBeNull();
    expect(
      root.querySelector("button[data-action=\"boost_4h\"]"),
    ).toBeNull();
    expect(getButton(root, "record")).toBeTruthy();
  });

  it("shows the degraded notice when callService is unavailable", async () => {
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    card.hass = makeHass(undefined);
    const root = await mount(card);
    expect(root.textContent).toContain("Service calls unavailable");
    expect(getButton(root, "analyze").disabled).toBe(true);
  });

  it("renders French labels when hass.locale.language is fr", async () => {
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    card.hass = makeHass(vi.fn().mockResolvedValue(undefined), "fr-FR");
    const root = await mount(card);
    expect(root.textContent).toContain("Analyser");
  });
});

describe("service calls", () => {
  function setup(
    impl?: (
      domain: string,
      service: string,
      data?: Record<string, unknown>,
    ) => Promise<unknown>,
  ): {
    card: PoolmanQuickActionsCard;
    calls: ServiceCall[];
    spy: ReturnType<typeof vi.fn>;
  } {
    const calls: ServiceCall[] = [];
    const spy = vi.fn(async (domain: string, service: string, data) => {
      calls.push({ domain, service, data });
      if (impl) return impl(domain, service, data);
      return undefined;
    });
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    card.hass = makeHass(spy);
    return { card, calls, spy };
  }

  it("'Analyze now' calls poolman.analyze with the device id", async () => {
    const { card, calls } = setup();
    const root = await mount(card);
    getButton(root, "analyze").click();
    await card.updateComplete;
    expect(calls).toEqual([
      { domain: "poolman", service: "analyze", data: { device_id: "dev1" } },
    ]);
  });

  it("'+2h' calls boost_filtration with hours=2", async () => {
    const { card, calls } = setup();
    const root = await mount(card);
    getButton(root, "boost_2h").click();
    await card.updateComplete;
    expect(calls).toEqual([
      {
        domain: "poolman",
        service: "boost_filtration",
        data: { device_id: "dev1", hours: 2 },
      },
    ]);
  });

  it("'+4h' calls boost_filtration with hours=4", async () => {
    const { card, calls } = setup();
    const root = await mount(card);
    getButton(root, "boost_4h").click();
    await card.updateComplete;
    expect(calls).toEqual([
      {
        domain: "poolman",
        service: "boost_filtration",
        data: { device_id: "dev1", hours: 4 },
      },
    ]);
  });

  it("flips to error state and shows a message when the service call fails", async () => {
    const { card } = setup(async () => {
      throw new Error("boom");
    });
    const root = await mount(card);
    getButton(root, "analyze").click();
    // Flush microtasks (promise rejection + state update) then re-render.
    for (let i = 0; i < 5; i++) {
      await Promise.resolve();
    }
    await card.updateComplete;
    const btn = getButton(root, "analyze");
    expect(btn.getAttribute("data-state")).toBe("error");
    const errMsg = root.querySelector(".qa-error-message");
    expect(errMsg?.textContent ?? "").toContain("boom");
  });
});

describe("record-treatment dialog", () => {
  function setup(): {
    card: PoolmanQuickActionsCard;
    calls: ServiceCall[];
  } {
    const calls: ServiceCall[] = [];
    const spy = vi.fn(async (domain: string, service: string, data) => {
      calls.push({ domain, service, data });
    });
    const card = new PoolmanQuickActionsCard();
    card.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    card.hass = makeHass(spy);
    return { card, calls };
  }

  async function openDialog(
    card: PoolmanQuickActionsCard,
  ): Promise<ShadowRoot> {
    const root = card.shadowRoot!;
    getButton(root, "record").click();
    await card.updateComplete;
    return root;
  }

  it("opens a dialog with the expected fields", async () => {
    const { card } = setup();
    await mount(card);
    const root = await openDialog(card);
    expect(root.querySelector("[role=\"dialog\"]")).toBeTruthy();
    expect(root.querySelector("#qa-type")).toBeTruthy();
    expect(root.querySelector("#qa-product")).toBeTruthy();
    expect(root.querySelector("#qa-quantity")).toBeTruthy();
    expect(root.querySelector("#qa-unit")).toBeTruthy();
    expect(root.querySelector("#qa-note")).toBeTruthy();
  });

  it("submits with stripped optional fields", async () => {
    const { card, calls } = setup();
    await mount(card);
    const root = await openDialog(card);

    const typeSelect = root.querySelector<HTMLSelectElement>("#qa-type")!;
    typeSelect.value = "cleaning";
    typeSelect.dispatchEvent(new Event("change"));

    const note = root.querySelector<HTMLTextAreaElement>("#qa-note")!;
    note.value = "skimmed";
    note.dispatchEvent(new Event("input"));

    await card.updateComplete;
    const submit = root.querySelector<HTMLButtonElement>(
      ".qa-dialog-actions button.primary",
    )!;
    submit.click();
    await new Promise((r) => setTimeout(r, 0));
    await card.updateComplete;

    expect(calls).toEqual([
      {
        domain: "poolman",
        service: "record_action",
        data: { device_id: "dev1", type: "cleaning", note: "skimmed" },
      },
    ]);
  });

  it("sends product/quantity/unit when provided and unit only with product", async () => {
    const { card, calls } = setup();
    await mount(card);
    const root = await openDialog(card);

    const product = root.querySelector<HTMLInputElement>("#qa-product")!;
    product.value = "chlorine-tabs";
    product.dispatchEvent(new Event("input"));

    const quantity = root.querySelector<HTMLInputElement>("#qa-quantity")!;
    quantity.value = "2";
    quantity.dispatchEvent(new Event("input"));

    const unit = root.querySelector<HTMLSelectElement>("#qa-unit")!;
    unit.value = "tablet";
    unit.dispatchEvent(new Event("change"));

    await card.updateComplete;
    root
      .querySelector<HTMLButtonElement>(".qa-dialog-actions button.primary")!
      .click();
    await new Promise((r) => setTimeout(r, 0));

    expect(calls).toHaveLength(1);
    expect(calls[0].service).toBe("record_action");
    expect(calls[0].data).toEqual({
      device_id: "dev1",
      type: "chemical",
      product_id: "chlorine-tabs",
      quantity: 2,
      unit: "tablet",
    });
  });

  it("rejects a negative quantity with an inline validation error", async () => {
    const { card, calls } = setup();
    await mount(card);
    const root = await openDialog(card);

    const quantity = root.querySelector<HTMLInputElement>("#qa-quantity")!;
    quantity.value = "-1";
    quantity.dispatchEvent(new Event("input"));

    await card.updateComplete;
    root
      .querySelector<HTMLButtonElement>(".qa-dialog-actions button.primary")!
      .click();
    await card.updateComplete;

    expect(calls).toHaveLength(0);
    expect(root.textContent).toContain("Quantity must be a positive number");
    // Dialog stays open.
    expect(root.querySelector("[role=\"dialog\"]")).toBeTruthy();
  });

  it("closes the dialog on Cancel without calling any service", async () => {
    const { card, calls } = setup();
    await mount(card);
    const root = await openDialog(card);

    const cancel = root.querySelector<HTMLButtonElement>(
      ".qa-dialog-actions button:not(.primary)",
    )!;
    cancel.click();
    await card.updateComplete;

    expect(root.querySelector("[role=\"dialog\"]")).toBeNull();
    expect(calls).toHaveLength(0);
  });
});
