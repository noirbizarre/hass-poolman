import { describe, expect, it, beforeAll } from "vitest";

import "../editor/poolman-problem-card-editor.js";
import { PoolmanProblemCardEditor } from "../editor/poolman-problem-card-editor.js";
import type { PoolProblemCardConfig } from "../types.js";
import {
  collectConfigChange,
  fakeHass,
  mountEditor,
  registerHaFormStub,
} from "./editor-helpers.js";

beforeAll(() => registerHaFormStub());

describe("poolman-problem-card-editor", () => {
  it("renders the expected schema fields", async () => {
    const editor = new PoolmanProblemCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const names = (form.schema as Array<{ name: string }>).map((s) => s.name);
    expect(names).toEqual(["device_id", "entity", "name", "max"]);
  });

  it("emits config-changed with merged values", async () => {
    const editor = new PoolmanProblemCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-problem-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const pending = collectConfigChange<PoolProblemCardConfig>(editor);
    form.emitChange({ max: 5 });
    const next = await pending;
    expect(next.max).toBe(5);
    expect(next.device_id).toBe("dev1");
  });
});
