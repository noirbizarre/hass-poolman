import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { problemCardStyles } from "./styles-problem.js";
import { firstPoolmanDeviceId } from "./editor/base.js";
import {
  formatExpectedRange,
  formatProblemValue,
  getEntity,
  isUnavailable,
  problemMetricLabel,
  readProblems,
  resolveEntities,
  severityPresentation,
} from "./helpers.js";
import type {
  HomeAssistant,
  PoolProblemCardConfig,
  ProblemDTO,
  ProblemSeverity,
  WorstSeverity,
} from "./types.js";

const CARD_TAG = "poolman-problem-card";

const WORST_PRESENTATION: Record<
  WorstSeverity,
  { label: string; color: string; icon: string }
> = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅",
  },
  low: severityPresentation("low"),
  medium: severityPresentation("medium"),
  critical: severityPresentation("critical"),
};

export class PoolmanProblemCard extends LitElement {
  static override styles = problemCardStyles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: PoolProblemCardConfig;

  /** Lovelace card size hint (1 unit ≈ 50px). */
  public getCardSize(): number {
    const entity = this._resolveEntity();
    if (!entity) return 1;
    const { count } = readProblems(entity);
    if (count === 0) return 1;
    const max = this._config?.max ?? count;
    return 1 + Math.min(count, max);
  }

  public static getStubConfig(hass?: HomeAssistant): Partial<PoolProblemCardConfig> {
    const deviceId = firstPoolmanDeviceId(hass);
    return {
      type: `custom:${CARD_TAG}`,
      ...(deviceId ? { device_id: deviceId } : {}),
    };
  }

  public static async getConfigElement(): Promise<HTMLElement> {
    await import("./editor/poolman-problem-card-editor.js");
    return document.createElement("poolman-problem-card-editor");
  }

  public setConfig(config: PoolProblemCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    if (!config.device_id && !config.entity) {
      throw new Error(
        "poolman-problem-card: either `device_id` or `entity` must be provided",
      );
    }
    if (config.max !== undefined && (!Number.isFinite(config.max) || config.max < 1)) {
      throw new Error("poolman-problem-card: `max` must be a positive integer");
    }
    this._config = { ...config };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;

    const entity = this._resolveEntity();
    const title = this._config.name ?? this._deviceName() ?? "Pool Problems";

    if (!entity || isUnavailable(entity)) {
      return html`
        <ha-card>
          <div class="header">
            <div class="title">
              <span class="icon" aria-hidden="true">🩺</span>
              <span>${title}</span>
            </div>
          </div>
          <div class="unavailable" role="status">
            <span aria-hidden="true">❔</span>
            <span>Problems entity unavailable</span>
          </div>
        </ha-card>
      `;
    }

    const { count, list, worst } = readProblems(entity);
    const worstMeta = WORST_PRESENTATION[worst] ?? WORST_PRESENTATION.ok;

    return html`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">🩺</span>
            <span>${title}</span>
          </div>
          <span
            class="badge"
            style=${`background:${worstMeta.color}`}
            role="status"
            aria-label=${`Worst severity: ${worstMeta.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${worstMeta.label}
          </span>
        </div>

        ${count === 0
          ? html`
              <div class="empty" role="status">
                <span aria-hidden="true">✅</span>
                <span>No problems detected — pool is healthy</span>
              </div>
            `
          : this._renderProblems(list, count)}
      </ha-card>
    `;
  }

  private _renderProblems(
    list: ProblemDTO[],
    count: number,
  ): TemplateResult {
    const max = this._config?.max;
    const shown = max !== undefined ? list.slice(0, max) : list;
    const hidden = Math.max(0, count - shown.length);
    return html`
      <div class="problems">
        ${shown.map((problem) => this._renderProblem(problem))}
        ${hidden > 0
          ? html`<div class="more">
              +${hidden} more problem${hidden === 1 ? "" : "s"}
            </div>`
          : nothing}
      </div>
    `;
  }

  private _renderProblem(problem: ProblemDTO): TemplateResult {
    const severity: ProblemSeverity = problem.severity;
    const meta = severityPresentation(severity);
    const metricLabel = problemMetricLabel(problem.metric);
    const hasNumerics =
      problem.metric !== null &&
      problem.value !== null &&
      problem.expected_range !== null;
    return html`
      <div
        class="problem"
        data-code=${problem.code}
        data-severity=${severity}
        style=${`--problem-color:${meta.color}`}
      >
        <span class="severity" aria-label=${`Severity: ${meta.label}`}>
          <span aria-hidden="true">${meta.icon}</span>
          ${meta.label}
        </span>
        <span class="message">${problem.message}</span>
        ${hasNumerics
          ? html`
              <div class="details">
                ${metricLabel
                  ? html`<span class="metric-label">${metricLabel}</span>
                      <span class="sep" aria-hidden="true">•</span>`
                  : nothing}
                <span>
                  Current:
                  <strong>${formatProblemValue(problem.metric, problem.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${formatExpectedRange(problem.metric, problem.expected_range)}</strong
                  >
                </span>
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _resolveEntity() {
    if (!this.hass || !this._config) return undefined;
    if (this._config.entity) {
      return getEntity(this.hass, this._config.entity);
    }
    const resolved = resolveEntities(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id,
    });
    return getEntity(this.hass, resolved.problems);
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
  customElements.define(CARD_TAG, PoolmanProblemCard);
}
