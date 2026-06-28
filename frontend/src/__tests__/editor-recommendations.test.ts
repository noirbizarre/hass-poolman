import { describe, expect, it, beforeAll } from "vitest";

import "../editor/poolman-recommendations-card-editor.js";
import { PoolmanRecommendationsCardEditor } from "../editor/poolman-recommendations-card-editor.js";
import type { PoolRecommendationsCardConfig } from "../types.js";
import {
  collectConfigChange,
  fakeHass,
  mountEditor,
  registerHaFormStub,
} from "./editor-helpers.js";

beforeAll(() => registerHaFormStub());

describe("poolman-recommendations-card-editor", () => {
  it("defaults confirm_apply to critical_high", async () => {
    const editor = new PoolmanRecommendationsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    expect((form.data as PoolRecommendationsCardConfig).confirm_apply).toBe(
      "critical_high",
    );
    expect((form.data as PoolRecommendationsCardConfig).show_severity).toBe(true);
  });

  it("exposes confirm_apply choices", async () => {
    const editor = new PoolmanRecommendationsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const schema = form.schema as Array<{
      name: string;
      selector?: { select?: { options?: Array<{ value: string }> } };
    }>;
    const confirm = schema.find((s) => s.name === "confirm_apply");
    expect(confirm).toBeDefined();
    expect(confirm?.selector?.select?.options?.map((o) => o.value)).toEqual([
      "never",
      "always",
      "critical_high",
    ]);
  });

  it("forwards value-changed as config-changed", async () => {
    const editor = new PoolmanRecommendationsCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-recommendations-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const pending = collectConfigChange<PoolRecommendationsCardConfig>(editor);
    form.emitChange({ confirm_apply: "always" });
    const next = await pending;
    expect(next.confirm_apply).toBe("always");
  });
});
