import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { t } from "../i18n.js";
import type { HomeAssistant, PoolOverviewCardConfig } from "../types.js";
import {
  boolSelector,
  deviceSelector,
  fireConfigChanged,
  makeComputeLabel,
  textSelector,
  type SchemaItem,
} from "./base.js";

export const POOL_OVERVIEW_EDITOR_TAG = "poolman-pool-overview-card-editor";

const METRIC_OPTIONS = [
  { value: "temperature", label_key: "editor_metric_temperature" as const },
  { value: "ph", label_key: "editor_metric_ph" as const },
  { value: "free_chlorine", label_key: "editor_metric_free_chlorine" as const },
  { value: "orp", label_key: "editor_metric_orp" as const },
];

export class PoolmanPoolOverviewCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolOverviewCardConfig;

  public setConfig(config: PoolOverviewCardConfig): void {
    this._config = { ...config };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config) return nothing;

    const lang = this.hass?.locale?.language;
    const schema: SchemaItem[] = [
      { name: "device_id", selector: deviceSelector },
      { name: "name", selector: textSelector },
      {
        name: "metrics",
        selector: {
          select: {
            multiple: true,
            mode: "list",
            options: METRIC_OPTIONS.map((m) => ({
              value: m.value,
              label: t(lang, m.label_key),
            })),
          },
        },
      },
      { name: "show_score", selector: boolSelector, default: true },
      { name: "recommendations_path", selector: textSelector },
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

  private _onValueChanged = (ev: CustomEvent<{ value: PoolOverviewCardConfig }>): void => {
    ev.stopPropagation();
    if (!this._config) return;
    const next: PoolOverviewCardConfig = { ...this._config, ...ev.detail.value };
    this._config = next;
    fireConfigChanged(this, next);
  };
}

if (!customElements.get(POOL_OVERVIEW_EDITOR_TAG)) {
  customElements.define(POOL_OVERVIEW_EDITOR_TAG, PoolmanPoolOverviewCardEditor);
}
