import { describe, expect, it, beforeAll } from "vitest";

import "../editor/poolman-pool-overview-card-editor.js";
import { PoolmanPoolOverviewCardEditor } from "../editor/poolman-pool-overview-card-editor.js";
import type { PoolOverviewCardConfig } from "../types.js";
import {
  collectConfigChange,
  fakeHass,
  mountEditor,
  registerHaFormStub,
} from "./editor-helpers.js";

beforeAll(() => registerHaFormStub());

describe("poolman-pool-overview-card-editor", () => {
  it("clones the config passed to setConfig", () => {
    const editor = new PoolmanPoolOverviewCardEditor();
    const cfg: PoolOverviewCardConfig = {
      type: "custom:poolman-pool-overview-card",
      device_id: "dev1",
    };
    editor.setConfig(cfg);
    cfg.device_id = "mutated";
    // Trigger a render so we can inspect data.
    editor.hass = fakeHass();
    return mountEditor(editor).then(({ form }) => {
      expect((form.data as PoolOverviewCardConfig).device_id).toBe("dev1");
    });
  });

  it("renders the expected schema fields", async () => {
    const editor = new PoolmanPoolOverviewCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-pool-overview-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const schema = form.schema as Array<{ name: string }>;
    const names = schema.map((s) => s.name);
    expect(names).toEqual([
      "device_id",
      "name",
      "metrics",
      "show_score",
      "recommendations_path",
    ]);
  });

  it("forwards value-changed as a config-changed event", async () => {
    const editor = new PoolmanPoolOverviewCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-pool-overview-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const pending = collectConfigChange<PoolOverviewCardConfig>(editor);
    form.emitChange({ name: "Pretty Pool", show_score: false });
    const next = await pending;
    expect(next.name).toBe("Pretty Pool");
    expect(next.show_score).toBe(false);
    expect(next.device_id).toBe("dev1");
  });
});
