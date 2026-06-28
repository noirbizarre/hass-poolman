import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { t } from "../i18n.js";
import type { HomeAssistant, QuickActionsCardConfig } from "../types.js";
import {
  boolSelector,
  deviceSelector,
  fireConfigChanged,
  makeComputeLabel,
  textSelector,
  type SchemaItem,
} from "./base.js";

export const QUICK_ACTIONS_EDITOR_TAG = "poolman-quick-actions-card-editor";

export class PoolmanQuickActionsCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: QuickActionsCardConfig;

  public setConfig(config: QuickActionsCardConfig): void {
    this._config = {
      analyze: config.analyze ?? true,
      boost: config.boost ?? true,
      record: config.record ?? true,
      ...config,
    };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config) return nothing;
    const lang = this.hass?.locale?.language;
    const schema: SchemaItem[] = [
      { name: "device_id", required: true, selector: deviceSelector },
      { name: "name", selector: textSelector },
      { name: "analyze", selector: boolSelector, default: true },
      { name: "boost", selector: boolSelector, default: true },
      { name: "record", selector: boolSelector, default: true },
    ];

    const missingDevice = !this._config.device_id;

    return html`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${schema}
        .computeLabel=${makeComputeLabel(lang)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
      <p
        class="poolman-editor-error"
        role="alert"
        ?hidden=${!missingDevice}
      >
        ${t(lang, "editor_device_required")}
      </p>
    `;
  }

  private _onValueChanged = (ev: CustomEvent<{ value: QuickActionsCardConfig }>): void => {
    ev.stopPropagation();
    if (!this._config) return;
    const next: QuickActionsCardConfig = { ...this._config, ...ev.detail.value };
    this._config = next;
    fireConfigChanged(this, next);
  };
}

if (!customElements.get(QUICK_ACTIONS_EDITOR_TAG)) {
  customElements.define(QUICK_ACTIONS_EDITOR_TAG, PoolmanQuickActionsCardEditor);
}
