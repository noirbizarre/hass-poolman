// Shared test utilities for the Poolman visual editor unit tests.
//
// Each editor renders an HA-native `<ha-form>` element fed with a selector
// schema. In tests we register a tiny stub `<ha-form>` that records the
// last `.schema`, `.data` and `.computeLabel` assigned to it and exposes a
// helper to dispatch a synthetic `value-changed` event back to the editor.

interface StubHaForm extends HTMLElement {
  schema?: unknown;
  data?: unknown;
  hass?: unknown;
  computeLabel?: (item: { name: string }) => string;
  emitChange: (value: Record<string, unknown>) => void;
}

class HaFormStub extends HTMLElement {
  schema?: unknown;
  data?: unknown;
  hass?: unknown;
  computeLabel?: (item: { name: string }) => string;

  emitChange(value: Record<string, unknown>): void {
    this.dispatchEvent(
      new CustomEvent("value-changed", {
        detail: { value },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

let registered = false;

export function registerHaFormStub(): void {
  if (registered) return;
  registered = true;
  if (!customElements.get("ha-form")) {
    customElements.define("ha-form", HaFormStub);
  }
}

export async function mountEditor<T extends HTMLElement>(editor: T): Promise<{
  root: ShadowRoot;
  form: StubHaForm;
}> {
  document.body.appendChild(editor);
  // Lit elements expose `updateComplete` promise.
  await (editor as unknown as { updateComplete?: Promise<unknown> }).updateComplete;
  const root = (editor as unknown as { shadowRoot: ShadowRoot }).shadowRoot;
  const form = root.querySelector("ha-form") as StubHaForm | null;
  if (!form) throw new Error("ha-form not rendered");
  return { root, form };
}

export function fakeHass(language = "en"): {
  states: Record<string, never>;
  entities: Record<string, never>;
  devices: Record<string, { id: string; name: string; name_by_user: null }>;
  locale: { language: string };
} {
  return {
    states: {},
    entities: {},
    devices: {
      dev1: { id: "dev1", name: "Demo Pool", name_by_user: null },
    },
    locale: { language },
  };
}

export function collectConfigChange<T>(target: HTMLElement): Promise<T> {
  return new Promise((resolve) => {
    target.addEventListener(
      "config-changed",
      (ev) => resolve((ev as CustomEvent<{ config: T }>).detail.config),
      { once: true },
    );
  });
}
