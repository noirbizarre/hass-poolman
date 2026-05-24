import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { quickActionsStyles } from "./quick-actions-styles.js";
import { t, type TranslationKey } from "./i18n.js";
import {
  INVENTORY_UNITS,
  type HomeAssistant,
  type QuickActionsCardConfig,
  type RecordActionType,
} from "./types.js";

export const QUICK_ACTIONS_CARD_TAG = "poolman-quick-actions-card";

const POOLMAN_DOMAIN = "poolman";
const SERVICE_ANALYZE = "analyze";
const SERVICE_BOOST_FILTRATION = "boost_filtration";
const SERVICE_RECORD_ACTION = "record_action";

const SUCCESS_RESET_MS = 1500;
const ERROR_RESET_MS = 3000;

type ButtonId = "analyze" | "boost_2h" | "boost_4h" | "record";
type ButtonState = "idle" | "pending" | "success" | "error";

interface RecordActionDraft {
  type: RecordActionType;
  product_id: string;
  quantity: string;
  unit: string;
  note: string;
}

const EMPTY_DRAFT: RecordActionDraft = {
  type: "chemical",
  product_id: "",
  quantity: "",
  unit: "",
  note: "",
};

export class PoolmanQuickActionsCard extends LitElement {
  static override styles = quickActionsStyles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: QuickActionsCardConfig;
  @state() private _states: Partial<Record<ButtonId, ButtonState>> = {};
  @state() private _errors: Partial<Record<ButtonId, string>> = {};
  @state() private _dialogOpen = false;
  @state() private _draft: RecordActionDraft = { ...EMPTY_DRAFT };
  @state() private _validationError = "";

  private _resetTimers: Partial<Record<ButtonId, ReturnType<typeof setTimeout>>> =
    {};

  public override disconnectedCallback(): void {
    super.disconnectedCallback();
    for (const id of Object.keys(this._resetTimers) as ButtonId[]) {
      const timer = this._resetTimers[id];
      if (timer) clearTimeout(timer);
    }
    this._resetTimers = {};
  }

  /** Lovelace card size hint (1 unit ≈ 50px). */
  public getCardSize(): number {
    return 2;
  }

  public static getStubConfig(
    hass?: HomeAssistant,
  ): Partial<QuickActionsCardConfig> {
    const deviceId = hass?.devices
      ? Object.keys(hass.devices)[0]
      : undefined;
    return {
      type: `custom:${QUICK_ACTIONS_CARD_TAG}`,
      device_id: deviceId ?? "",
    };
  }

  public setConfig(config: QuickActionsCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    if (!config.device_id) {
      throw new Error(
        "poolman-quick-actions-card: `device_id` is required",
      );
    }
    this._config = {
      analyze: true,
      boost: true,
      record: true,
      ...config,
    };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;

    const lang = this.hass.locale?.language;
    const title =
      this._config.name ??
      this._deviceName(this._config.device_id) ??
      t(lang, "card_name");

    const callable = typeof this.hass.callService === "function";

    return html`
      <ha-card>
        <div class="header">${title}</div>
        ${callable
          ? nothing
          : html`<div class="qa-notice" role="status">
              ${t(lang, "service_unavailable")}
            </div>`}
        <div class="buttons">
          ${this._config.analyze !== false
            ? this._renderButton("analyze", "🔍", "analyze", "analyze_aria", () =>
                this._invokeAnalyze(),
              )
            : nothing}
          ${this._config.boost !== false
            ? [
                this._renderButton(
                  "boost_2h",
                  "⏱",
                  "boost_2h",
                  "boost_aria",
                  () => this._invokeBoost(2, "boost_2h"),
                ),
                this._renderButton(
                  "boost_4h",
                  "⏱",
                  "boost_4h",
                  "boost_aria",
                  () => this._invokeBoost(4, "boost_4h"),
                ),
              ]
            : nothing}
          ${this._config.record !== false
            ? this._renderButton(
                "record",
                "🧪",
                "record",
                "record_aria",
                () => this._openDialog(),
              )
            : nothing}
          ${this._renderErrors()}
        </div>
        ${this._dialogOpen ? this._renderDialog() : nothing}
      </ha-card>
    `;
  }

  // ---- button rendering ----------------------------------------------------

  private _renderButton(
    id: ButtonId,
    icon: string,
    labelKey: TranslationKey,
    ariaKey: TranslationKey,
    onTap: () => void,
  ): TemplateResult {
    const lang = this.hass?.locale?.language;
    const state = this._states[id] ?? "idle";
    const disabled =
      state === "pending" || typeof this.hass?.callService !== "function";
    const label =
      state === "pending"
        ? t(lang, "pending")
        : state === "success"
          ? t(lang, "success")
          : t(lang, labelKey);
    return html`
      <button
        type="button"
        class="qa-btn"
        data-action=${id}
        data-state=${state}
        aria-label=${t(lang, ariaKey)}
        ?disabled=${disabled}
        @click=${onTap}
      >
        ${state === "pending"
          ? html`<span class="qa-spinner" aria-hidden="true"></span>`
          : html`<span class="qa-icon" aria-hidden="true">${icon}</span>`}
        <span class="qa-label">${label}</span>
      </button>
    `;
  }

  private _renderErrors(): TemplateResult[] | typeof nothing {
    const entries = (Object.entries(this._errors) as Array<[ButtonId, string]>).filter(
      ([, msg]) => Boolean(msg),
    );
    if (entries.length === 0) return nothing;
    return entries.map(
      ([id, msg]) => html`
        <div class="qa-error-message" role="alert" data-action=${id}>
          ${msg}
        </div>
      `,
    );
  }

  // ---- dialog rendering ----------------------------------------------------

  private _renderDialog(): TemplateResult {
    const lang = this.hass?.locale?.language;
    const submitting = this._states.record === "pending";
    return html`
      <div
        class="qa-dialog-backdrop"
        role="presentation"
        @click=${(ev: MouseEvent) => {
          if (ev.target === ev.currentTarget && !submitting) this._closeDialog();
        }}
      >
        <div
          class="qa-dialog"
          role="dialog"
          aria-modal="true"
          aria-label=${t(lang, "dialog_title")}
        >
          <h2>${t(lang, "dialog_title")}</h2>

          <div class="qa-field">
            <label for="qa-type">${t(lang, "dialog_type")}</label>
            <select
              id="qa-type"
              .value=${this._draft.type}
              @change=${(ev: Event) =>
                this._updateDraft({
                  type: (ev.target as HTMLSelectElement).value as RecordActionType,
                })}
            >
              <option value="chemical">
                ${t(lang, "dialog_type_chemical")}
              </option>
              <option value="cleaning">
                ${t(lang, "dialog_type_cleaning")}
              </option>
              <option value="maintenance">
                ${t(lang, "dialog_type_maintenance")}
              </option>
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-product">${t(lang, "dialog_product_id")}</label>
            <input
              id="qa-product"
              type="text"
              .value=${this._draft.product_id}
              @input=${(ev: Event) =>
                this._updateDraft({
                  product_id: (ev.target as HTMLInputElement).value,
                })}
            />
          </div>

          <div class="qa-field">
            <label for="qa-quantity">${t(lang, "dialog_quantity")}</label>
            <input
              id="qa-quantity"
              type="number"
              min="0"
              step="any"
              inputmode="decimal"
              .value=${this._draft.quantity}
              @input=${(ev: Event) =>
                this._updateDraft({
                  quantity: (ev.target as HTMLInputElement).value,
                })}
            />
          </div>

          <div class="qa-field">
            <label for="qa-unit">${t(lang, "dialog_unit")}</label>
            <select
              id="qa-unit"
              .value=${this._draft.unit}
              @change=${(ev: Event) =>
                this._updateDraft({
                  unit: (ev.target as HTMLSelectElement).value,
                })}
            >
              <option value="">${t(lang, "dialog_unit_none")}</option>
              ${INVENTORY_UNITS.map(
                (u) => html`<option value=${u}>${u}</option>`,
              )}
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-note">${t(lang, "dialog_note")}</label>
            <textarea
              id="qa-note"
              .value=${this._draft.note}
              @input=${(ev: Event) =>
                this._updateDraft({
                  note: (ev.target as HTMLTextAreaElement).value,
                })}
            ></textarea>
          </div>

          ${this._validationError
            ? html`<div class="qa-validation" role="alert">
                ${this._validationError}
              </div>`
            : nothing}

          <div class="qa-dialog-actions">
            <button
              type="button"
              ?disabled=${submitting}
              @click=${() => this._closeDialog()}
            >
              ${t(lang, "dialog_cancel")}
            </button>
            <button
              type="button"
              class="primary"
              ?disabled=${submitting}
              @click=${() => this._submitDialog()}
            >
              ${t(lang, "dialog_submit")}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // ---- service calls -------------------------------------------------------

  private async _invokeAnalyze(): Promise<void> {
    const device_id = this._config?.device_id;
    if (!device_id) return;
    await this._runService("analyze", SERVICE_ANALYZE, { device_id });
  }

  private async _invokeBoost(hours: number, id: ButtonId): Promise<void> {
    const device_id = this._config?.device_id;
    if (!device_id) return;
    await this._runService(id, SERVICE_BOOST_FILTRATION, { device_id, hours });
  }

  private async _runService(
    id: ButtonId,
    service: string,
    data: Record<string, unknown>,
  ): Promise<boolean> {
    const callService = this.hass?.callService;
    if (typeof callService !== "function") return false;

    this._clearError(id);
    this._setState(id, "pending");
    try {
      await callService(POOLMAN_DOMAIN, service, data);
      this._setState(id, "success");
      this._scheduleReset(id, SUCCESS_RESET_MS);
      return true;
    } catch (err) {
      const lang = this.hass?.locale?.language;
      const msg = err instanceof Error && err.message
        ? err.message
        : t(lang, "error_generic");
      this._setError(id, msg);
      this._setState(id, "error");
      this._scheduleReset(id, ERROR_RESET_MS);
      return false;
    }
  }

  // ---- dialog state --------------------------------------------------------

  private _openDialog(): void {
    this._draft = { ...EMPTY_DRAFT };
    this._validationError = "";
    this._clearError("record");
    this._dialogOpen = true;
  }

  private _closeDialog(): void {
    this._dialogOpen = false;
    this._validationError = "";
  }

  private _updateDraft(patch: Partial<RecordActionDraft>): void {
    this._draft = { ...this._draft, ...patch };
    if (this._validationError) this._validationError = "";
  }

  private async _submitDialog(): Promise<void> {
    const lang = this.hass?.locale?.language;
    const device_id = this._config?.device_id;
    if (!device_id) return;

    const payload: Record<string, unknown> = {
      device_id,
      type: this._draft.type,
    };

    const productId = this._draft.product_id.trim();
    if (productId) payload.product_id = productId;

    const quantityRaw = this._draft.quantity.trim();
    if (quantityRaw !== "") {
      const quantity = Number(quantityRaw);
      if (!Number.isFinite(quantity) || quantity < 0) {
        this._validationError = t(lang, "dialog_validation_quantity");
        return;
      }
      payload.quantity = quantity;
    }

    const unit = this._draft.unit.trim();
    // Only send unit when a product is provided (mirrors service semantics).
    if (unit && productId) payload.unit = unit;

    const note = this._draft.note.trim();
    if (note) payload.note = note;

    const ok = await this._runService("record", SERVICE_RECORD_ACTION, payload);
    if (ok) this._closeDialog();
  }

  // ---- helpers -------------------------------------------------------------

  private _setState(id: ButtonId, state: ButtonState): void {
    this._states = { ...this._states, [id]: state };
  }

  private _setError(id: ButtonId, message: string): void {
    this._errors = { ...this._errors, [id]: message };
  }

  private _clearError(id: ButtonId): void {
    if (!this._errors[id]) return;
    const next = { ...this._errors };
    delete next[id];
    this._errors = next;
  }

  private _scheduleReset(id: ButtonId, delay: number): void {
    const existing = this._resetTimers[id];
    if (existing) clearTimeout(existing);
    this._resetTimers[id] = setTimeout(() => {
      this._setState(id, "idle");
      this._clearError(id);
      delete this._resetTimers[id];
    }, delay);
  }

  private _deviceName(deviceId: string | undefined): string | undefined {
    if (!deviceId || !this.hass?.devices) return undefined;
    const device = this.hass.devices[deviceId];
    if (!device) return undefined;
    return device.name_by_user ?? device.name ?? undefined;
  }
}

if (!customElements.get(QUICK_ACTIONS_CARD_TAG)) {
  customElements.define(QUICK_ACTIONS_CARD_TAG, PoolmanQuickActionsCard);
}
