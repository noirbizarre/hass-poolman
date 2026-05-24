import { LitElement, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { recommendationsCardStyles } from "./styles.js";
import {
  getEntity,
  isUnavailable,
  priorityPresentation,
  readRecommendations,
  recommendationPriority,
  recommendationTreatments,
  resolveRecommendationsEntity,
} from "./helpers.js";
import type {
  ConfirmApplyMode,
  HomeAssistant,
  PoolRecommendationsCardConfig,
  RecommendationDTO,
} from "./types.js";

const CARD_TAG = "poolman-recommendations-card";

/**
 * Lovelace card listing active pool recommendations.
 *
 * Reads the `recommendations` attribute of `sensor.<pool>_recommendations`
 * and renders one expandable row per recommendation with an "Apply" button
 * that calls the `poolman.apply_recommendation` service.
 */
export class PoolmanRecommendationsCard extends LitElement {
  static override styles = recommendationsCardStyles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolRecommendationsCardConfig;
  /** Recommendation ids dismissed via the per-instance "Ignore" button. */
  @state() private _dismissed: Set<string> = new Set();
  /** Recommendation ids currently expanded in the UI. */
  @state() private _expanded: Set<string> = new Set();

  /** Set of recommendation ids seen on the most recent render, used to purge
   *  stale entries from `_dismissed` when the backend no longer emits them. */
  private _lastSeenIds: Set<string> = new Set();

  /** Lovelace card size hint (1 unit ≈ 50px). */
  public getCardSize(): number {
    return 4;
  }

  public static getStubConfig(): Partial<PoolRecommendationsCardConfig> {
    return { type: `custom:${CARD_TAG}` };
  }

  public setConfig(config: PoolRecommendationsCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    if (!config.device_id && !config.entity) {
      throw new Error(
        "poolman-recommendations-card: either `device_id` or `entity` must be provided",
      );
    }
    const mode: ConfirmApplyMode = config.confirm_apply ?? "critical_high";
    this._config = {
      show_severity: true,
      ...config,
      confirm_apply: mode,
    };
  }

  protected override updated(_changed: PropertyValues): void {
    // When a previously-dismissed recommendation disappears from the entity
    // attributes, purge it from the dismissed set so the user sees it again
    // if it is re-emitted later.
    if (this._dismissed.size === 0) return;
    let mutated = false;
    for (const id of this._dismissed) {
      if (!this._lastSeenIds.has(id)) {
        this._dismissed.delete(id);
        mutated = true;
      }
    }
    if (mutated) {
      // Trigger a re-render with the cleaned dismissed set.
      this._dismissed = new Set(this._dismissed);
    }
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;

    const entityId = resolveRecommendationsEntity(this.hass, this._config);
    const entity = getEntity(this.hass, entityId);
    const title = this._config.name ?? this._deviceName() ?? "Recommendations";

    if (!entity || isUnavailable(entity)) {
      return html`
        <ha-card>
          <div class="header">
            <div class="title">
              <span class="icon" aria-hidden="true">📋</span>
              <span>${title}</span>
            </div>
          </div>
          <div class="unavailable" role="status">
            <span aria-hidden="true">⚠️</span>
            Recommendations unavailable
          </div>
        </ha-card>
      `;
    }

    const { count, list } = readRecommendations(entity);
    // Track ids seen so `updated()` can purge stale dismissals.
    this._lastSeenIds = new Set(list.map((r) => r.id));
    const visible = list.filter((r) => !this._dismissed.has(r.id));

    return html`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">📋</span>
            <span>${title}</span>
          </div>
          ${count > 0
            ? html`<span class="count">${visible.length} / ${count}</span>`
            : nothing}
        </div>

        ${visible.length === 0
          ? this._renderEmpty()
          : html`<div class="list">${visible.map((r) => this._renderRecommendation(r))}</div>`}
      </ha-card>
    `;
  }

  private _renderEmpty(): TemplateResult {
    return html`
      <div class="empty" role="status">
        <span aria-hidden="true">✅</span>
        Your pool is in good condition
      </div>
    `;
  }

  private _renderRecommendation(rec: RecommendationDTO): TemplateResult {
    const meta = priorityPresentation(rec);
    const expanded = this._expanded.has(rec.id);
    const showSeverity = this._config?.show_severity !== false;
    const treatments = recommendationTreatments(rec);
    return html`
      <div
        class="rec"
        data-id=${rec.id}
        data-priority=${meta.key}
        style=${`--rec-color:${meta.color}`}
      >
        <div
          class="rec-head"
          role="button"
          tabindex="0"
          aria-expanded=${expanded ? "true" : "false"}
          @click=${() => this._toggle(rec.id)}
          @keydown=${(ev: KeyboardEvent) => {
            if (ev.key === "Enter" || ev.key === " ") {
              ev.preventDefault();
              this._toggle(rec.id);
            }
          }}
        >
          <span
            class="badge"
            aria-label=${`Priority: ${meta.label}`}
          >
            <span aria-hidden="true">${meta.icon}</span>
            ${showSeverity ? html`<span>${meta.label}</span>` : nothing}
          </span>
          <span class="rec-text">
            <span class="rec-title">${rec.title}</span>
            ${rec.description
              ? html`<span class="rec-desc">${rec.description}</span>`
              : nothing}
          </span>
          <span
            class=${`chevron ${expanded ? "open" : ""}`}
            aria-hidden="true"
          >›</span>
        </div>
        ${expanded ? this._renderDetail(rec, treatments) : nothing}
        <div class="rec-actions">
          <button
            class="btn ignore"
            type="button"
            @click=${(ev: Event) => {
              ev.stopPropagation();
              this._ignore(rec.id);
            }}
          >
            Ignore
          </button>
          <button
            class="btn apply"
            type="button"
            @click=${(ev: Event) => {
              ev.stopPropagation();
              void this._apply(rec);
            }}
          >
            Apply
          </button>
        </div>
      </div>
    `;
  }

  private _renderDetail(
    rec: RecommendationDTO,
    treatments: ReturnType<typeof recommendationTreatments>,
  ): TemplateResult {
    return html`
      <div class="rec-detail">
        ${rec.reason
          ? html`<div class="rec-reason"><strong>Reason:</strong> ${rec.reason}</div>`
          : nothing}
        ${treatments.length > 0
          ? html`
              <ul class="treatments" aria-label="Treatments">
                ${treatments.map(
                  (t) => html`
                    <li>
                      <span class="treatment-product">${t.name}</span>
                      <span class="treatment-qty"
                        >${this._formatQuantity(t.quantity)} ${t.unit}</span
                      >
                    </li>
                  `,
                )}
              </ul>
            `
          : nothing}
        ${rec.related_metrics && rec.related_metrics.length > 0
          ? html`
              <div class="metrics-row">
                ${rec.related_metrics.map(
                  (m) => html`<span class="metric-chip">${m}</span>`,
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _toggle(id: string): void {
    const next = new Set(this._expanded);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this._expanded = next;
  }

  private _formatQuantity(quantity: number): string {
    if (!Number.isFinite(quantity)) return String(quantity ?? "");
    const lang = this.hass?.locale?.language ?? "en";
    return quantity.toLocaleString(lang, { maximumFractionDigits: 2 });
  }

  private _ignore(id: string): void {
    const next = new Set(this._dismissed);
    next.add(id);
    this._dismissed = next;
  }

  private async _apply(rec: RecommendationDTO): Promise<void> {
    if (!this.hass?.callService) return;
    const deviceId = this._config?.device_id;
    if (!deviceId) {
      // No device id => we cannot call the service. Fail loudly in the
      // developer console rather than silently swallowing the click.
      // eslint-disable-next-line no-console
      console.error(
        "poolman-recommendations-card: cannot apply recommendation without `device_id`",
      );
      return;
    }
    if (!this._shouldConfirm(rec)) {
      await this._callApply(deviceId, rec.id);
      return;
    }
    const confirmFn = (globalThis as { confirm?: (msg?: string) => boolean }).confirm;
    const ok = confirmFn
      ? confirmFn(`Apply "${rec.title}"?`)
      : true;
    if (ok) {
      await this._callApply(deviceId, rec.id);
    }
  }

  private async _callApply(deviceId: string, recommendationId: string): Promise<void> {
    try {
      await this.hass!.callService!("poolman", "apply_recommendation", {
        device_id: deviceId,
        recommendation_id: recommendationId,
      });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("poolman-recommendations-card: apply failed", err);
    }
  }

  private _shouldConfirm(rec: RecommendationDTO): boolean {
    const mode = this._config?.confirm_apply ?? "critical_high";
    if (mode === "never") return false;
    if (mode === "always") return true;
    const prio = recommendationPriority(rec);
    return prio === "critical" || prio === "high";
  }

  private _deviceName(): string | undefined {
    const deviceId = this._config?.device_id;
    if (!deviceId || !this.hass?.devices) return undefined;
    const device = this.hass.devices[deviceId];
    if (!device) return undefined;
    return device.name_by_user ?? device.name ?? undefined;
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, PoolmanRecommendationsCard);
}
