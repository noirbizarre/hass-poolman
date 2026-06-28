import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { cardStyles } from "./styles.js";
import { firstPoolmanDeviceId } from "./editor/base.js";
import {
  MISSING,
  effectiveMetrics,
  formatMetric,
  getEntity,
  isUnavailable,
  metricPresentation,
  readRecommendations,
  readStatus,
  resolveEntities,
  scoreSeverity,
  statusPresentation,
} from "./helpers.js";
import type {
  EntityKey,
  HomeAssistant,
  PoolOverviewCardConfig,
} from "./types.js";

const CARD_TAG = "poolman-pool-overview-card";

export class PoolmanPoolOverviewCard extends LitElement {
  static override styles = cardStyles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolOverviewCardConfig;

  /** Lovelace card size hint (1 unit ≈ 50px). */
  public getCardSize(): number {
    return 3;
  }

  public static getStubConfig(hass?: HomeAssistant): Partial<PoolOverviewCardConfig> {
    const deviceId = firstPoolmanDeviceId(hass);
    return {
      type: `custom:${CARD_TAG}`,
      ...(deviceId ? { device_id: deviceId } : {}),
    };
  }

  public static async getConfigElement(): Promise<HTMLElement> {
    await import("./editor/poolman-pool-overview-card-editor.js");
    return document.createElement("poolman-pool-overview-card-editor");
  }

  public setConfig(config: PoolOverviewCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    if (!config.device_id && !config.entities) {
      throw new Error(
        "poolman-pool-overview-card: either `device_id` or `entities` must be provided",
      );
    }
    this._config = { show_score: true, ...config };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;

    const resolved = resolveEntities(this.hass, this._config);
    const statusEntity = getEntity(this.hass, resolved.status);
    const status = readStatus(statusEntity);
    const statusMeta = statusPresentation(status);

    const poolName =
      this._config.name ??
      this._deviceName(this._config.device_id) ??
      "Pool";

    const metrics = effectiveMetrics(this._config, resolved, this.hass);

    return html`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${poolName}</span>
          </div>
          <span
            class="badge"
            style=${`background:${statusMeta.color}`}
            role="status"
            aria-label=${`Status: ${statusMeta.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${statusMeta.label}
          </span>
        </div>

        <div class="metrics">
          ${metrics.map((key) => this._renderMetric(key, resolved))}
        </div>

        ${this._config.show_score !== false
          ? this._renderScore(resolved.water_quality_score)
          : nothing}
        ${this._renderRecommendations(resolved.recommendations)}
      </ha-card>
    `;
  }

  private _renderMetric(
    key: ReturnType<typeof effectiveMetrics>[number],
    resolved: Partial<Record<EntityKey, string>>,
  ): TemplateResult {
    const meta = metricPresentation(key);
    const entity = getEntity(this.hass!, resolved[key]);
    const value = formatMetric(entity, meta.fractionDigits, meta.unitFallback);
    return html`
      <div class="metric" data-key=${key}>
        <span class="metric-label">
          <span aria-hidden="true">${meta.icon}</span>
          ${meta.label}
        </span>
        <span class="metric-value">${value}</span>
      </div>
    `;
  }

  private _renderScore(entityId: string | undefined): TemplateResult {
    const entity = getEntity(this.hass!, entityId);
    if (isUnavailable(entity)) {
      return html`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${MISSING}</strong>
          </div>
        </div>
      `;
    }
    const score = Math.max(0, Math.min(100, Number(entity!.state) || 0));
    const severity = scoreSeverity(score);
    return html`
      <div class="score">
        <div class="score-row">
          <span>Quality score</span>
          <strong>${score} / 100</strong>
        </div>
        <div class="score-bar">
          <div
            class="score-bar-fill ${severity === "good" ? "" : severity}"
            style=${`width:${score}%`}
          ></div>
        </div>
      </div>
    `;
  }

  private _renderRecommendations(
    entityId: string | undefined,
  ): TemplateResult | typeof nothing {
    const entity = getEntity(this.hass!, entityId);
    if (!entity) return nothing;
    const { count } = readRecommendations(entity);
    const navTarget = this._config?.recommendations_path;
    const interactive = count > 0;
    const label =
      count === 0
        ? "Your pool is in good condition"
        : `${count} recommendation${count === 1 ? "" : "s"}`;
    const icon = count === 0 ? "✅" : "⚠️";
    return html`
      <div
        class="recommendations"
        role=${interactive ? "button" : "presentation"}
        tabindex=${interactive ? "0" : "-1"}
        ?disabled=${!interactive}
        @click=${() => interactive && this._openRecommendations(entity.entity_id, navTarget)}
        @keydown=${(ev: KeyboardEvent) => {
          if (!interactive) return;
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this._openRecommendations(entity.entity_id, navTarget);
          }
        }}
      >
        <span class="label">
          <span aria-hidden="true">${icon}</span>
          ${label}
        </span>
        ${interactive ? html`<span class="chevron" aria-hidden="true">›</span>` : nothing}
      </div>
    `;
  }

  private _openRecommendations(entityId: string, navTarget: string | undefined): void {
    if (navTarget) {
      // Use HA's navigate event so the dashboard router handles the path.
      this.dispatchEvent(
        new CustomEvent("location-changed", {
          bubbles: true,
          composed: true,
          detail: { replace: false },
        }),
      );
      history.pushState(null, "", navTarget);
      return;
    }
    // Fall back to the standard more-info dialog on the recommendations sensor.
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId },
      }),
    );
  }

  private _deviceName(deviceId: string | undefined): string | undefined {
    if (!deviceId || !this.hass?.devices) return undefined;
    const device = this.hass.devices[deviceId];
    if (!device) return undefined;
    return device.name_by_user ?? device.name ?? undefined;
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, PoolmanPoolOverviewCard);
}
