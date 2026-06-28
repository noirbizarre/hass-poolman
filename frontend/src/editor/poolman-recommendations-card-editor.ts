import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { t } from "../i18n.js";
import type {
  ConfirmApplyMode,
  HomeAssistant,
  PoolRecommendationsCardConfig,
} from "../types.js";
import {
  boolSelector,
  deviceSelector,
  entitySelector,
  fireConfigChanged,
  makeComputeLabel,
  textSelector,
  type SchemaItem,
} from "./base.js";

export const RECOMMENDATIONS_EDITOR_TAG = "poolman-recommendations-card-editor";

const CONFIRM_MODES: ConfirmApplyMode[] = ["never", "always", "critical_high"];

export class PoolmanRecommendationsCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolRecommendationsCardConfig;

  public setConfig(config: PoolRecommendationsCardConfig): void {
    const mode: ConfirmApplyMode = config.confirm_apply ?? "critical_high";
    this._config = {
      show_severity: config.show_severity ?? true,
      ...config,
      confirm_apply: mode,
    };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config) return nothing;
    const lang = this.hass?.locale?.language;
    const schema: SchemaItem[] = [
      { name: "device_id", selector: deviceSelector },
      { name: "entity", selector: entitySelector("sensor") },
      { name: "name", selector: textSelector },
      { name: "show_severity", selector: boolSelector, default: true },
      {
        name: "confirm_apply",
        selector: {
          select: {
            mode: "dropdown",
            options: CONFIRM_MODES.map((value) => ({
              value,
              label: t(lang, `editor_confirm_apply_${value}` as const),
            })),
          },
        },
        default: "critical_high",
      },
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
    ev: CustomEvent<{ value: PoolRecommendationsCardConfig }>,
  ): void => {
    ev.stopPropagation();
    if (!this._config) return;
    const next: PoolRecommendationsCardConfig = {
      ...this._config,
      ...ev.detail.value,
    };
    this._config = next;
    fireConfigChanged(this, next);
  };
}

if (!customElements.get(RECOMMENDATIONS_EDITOR_TAG)) {
  customElements.define(RECOMMENDATIONS_EDITOR_TAG, PoolmanRecommendationsCardEditor);
}
