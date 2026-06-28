import { describe, expect, it, beforeAll } from "vitest";

import "../editor/poolman-action-history-card-editor.js";
import { PoolmanActionHistoryCardEditor } from "../editor/poolman-action-history-card-editor.js";
import type { ActionHistoryCardConfig } from "../types.js";
import {
  collectConfigChange,
  fakeHass,
  mountEditor,
  registerHaFormStub,
} from "./editor-helpers.js";

beforeAll(() => registerHaFormStub());

describe("poolman-action-history-card-editor", () => {
  it("applies show_source/group_by_day defaults", async () => {
    const editor = new PoolmanActionHistoryCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const data = form.data as ActionHistoryCardConfig;
    expect(data.show_source).toBe(true);
    expect(data.group_by_day).toBe(true);
  });

  it("renders the expected schema fields", async () => {
    const editor = new PoolmanActionHistoryCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const names = (form.schema as Array<{ name: string }>).map((s) => s.name);
    expect(names).toEqual([
      "device_id",
      "name",
      "limit",
      "show_source",
      "group_by_day",
    ]);
  });

  it("forwards value-changed as config-changed", async () => {
    const editor = new PoolmanActionHistoryCardEditor();
    editor.hass = fakeHass();
    editor.setConfig({
      type: "custom:poolman-action-history-card",
      device_id: "dev1",
    });
    const { form } = await mountEditor(editor);
    const pending = collectConfigChange<ActionHistoryCardConfig>(editor);
    form.emitChange({ limit: 12, group_by_day: false });
    const next = await pending;
    expect(next.limit).toBe(12);
    expect(next.group_by_day).toBe(false);
  });
});
