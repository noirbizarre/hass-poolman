import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import type { ActionHistoryCardConfig, HomeAssistant } from "../types.js";
import {
  boolSelector,
  deviceSelector,
  fireConfigChanged,
  makeComputeLabel,
  numberSelector,
  textSelector,
  type SchemaItem,
} from "./base.js";

export const ACTION_HISTORY_EDITOR_TAG = "poolman-action-history-card-editor";

export class PoolmanActionHistoryCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: ActionHistoryCardConfig;

  public setConfig(config: ActionHistoryCardConfig): void {
    this._config = {
      show_source: config.show_source ?? true,
      group_by_day: config.group_by_day ?? true,
      ...config,
    };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config) return nothing;
    const lang = this.hass?.locale?.language;
    const schema: SchemaItem[] = [
      { name: "device_id", selector: deviceSelector },
      { name: "name", selector: textSelector },
      { name: "limit", selector: numberSelector(1, 50, 1) },
      { name: "show_source", selector: boolSelector, default: true },
      { name: "group_by_day", selector: boolSelector, default: true },
    ];

    return html`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${schema}
        .computeLabel=${makeComputeLabel(lang)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
    `;
  }

  private _onValueChanged = (
    ev: CustomEvent<{ value: ActionHistoryCardConfig }>,
  ): void => {
    ev.stopPropagation();
    if (!this._config) return;
    const next: ActionHistoryCardConfig = { ...this._config, ...ev.detail.value };
    this._config = next;
    fireConfigChanged(this, next);
  };
}

if (!customElements.get(ACTION_HISTORY_EDITOR_TAG)) {
  customElements.define(ACTION_HISTORY_EDITOR_TAG, PoolmanActionHistoryCardEditor);
}
