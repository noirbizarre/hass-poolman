import { describe, expect, it, beforeAll } from "vitest";

import "../editor/poolman-quick-actions-card-editor.js";
import { PoolmanQuickActionsCardEditor } from "../editor/poolman-quick-actions-card-editor.js";
import type { QuickActionsCardConfig } from "../types.js";
import {
  collectConfigChange,
  fakeHass,
  mountEditor,
  registerHaFormStub,
} from "./editor-helpers.js";

beforeAll(() => registerHaFormStub());

describe("poolman-quick-actions-card-editor", () => {
  it("applies analyze/boost/record defaults", async () => {
    const editor = new PoolmanQuickActionsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const data = form.data as QuickActionsCardConfig;
    expect(data.analyze).toBe(true);
    expect(data.boost).toBe(true);
    expect(data.record).toBe(true);
  });

  it("surfaces a validation message when device_id is empty", async () => {
    const editor = new PoolmanQuickActionsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "",
    });
    const { root } = await mountEditor(editor);
    const error = root.querySelector<HTMLParagraphElement>(".poolman-editor-error");
    expect(error).not.toBeNull();
    expect(error?.hasAttribute("hidden")).toBe(false);
  });

  it("does not show the validation message when device_id is set", async () => {
    const editor = new PoolmanQuickActionsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    const { root } = await mountEditor(editor);
    const error = root.querySelector<HTMLParagraphElement>(".poolman-editor-error");
    expect(error?.hasAttribute("hidden")).toBe(true);
  });

  it("forwards value-changed as config-changed", async () => {
    const editor = new PoolmanQuickActionsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-quick-actions-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const pending = collectConfigChange<QuickActionsCardConfig>(editor);
    form.emitChange({ record: false, name: "Quick" });
    const next = await pending;
    expect(next.record).toBe(false);
    expect(next.name).toBe("Quick");
    expect(next.device_id).toBe("dev1");
  });
});
