import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import type { HomeAssistant, PoolProblemCardConfig } from "../types.js";
import {
  deviceSelector,
  entitySelector,
  fireConfigChanged,
  makeComputeLabel,
  numberSelector,
  textSelector,
  type SchemaItem,
} from "./base.js";

export const PROBLEM_EDITOR_TAG = "poolman-problem-card-editor";

export class PoolmanProblemCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolProblemCardConfig;

  public setConfig(config: PoolProblemCardConfig): void {
    this._config = { ...config };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config) return nothing;
    const lang = this.hass?.locale?.language;
    const schema: SchemaItem[] = [
      { name: "device_id", selector: deviceSelector },
      { name: "entity", selector: entitySelector("sensor") },
      { name: "name", selector: textSelector },
      { name: "max", selector: numberSelector(1, 50, 1) },
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

  private _onValueChanged = (ev: CustomEvent<{ value: PoolProblemCardConfig }>): void => {
    ev.stopPropagation();
    if (!this._config) return;
    const next: PoolProblemCardConfig = { ...this._config, ...ev.detail.value };
    this._config = next;
    fireConfigChanged(this, next);
  };
}

if (!customElements.get(PROBLEM_EDITOR_TAG)) {
  customElements.define(PROBLEM_EDITOR_TAG, PoolmanProblemCardEditor);
}
