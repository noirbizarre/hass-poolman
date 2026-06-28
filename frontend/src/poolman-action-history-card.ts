import { LitElement, html, nothing, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { actionHistoryStyles } from "./styles.js";
import { MISSING, getEntity, resolveEntities } from "./helpers.js";
import { firstPoolmanDeviceId } from "./editor/base.js";
import type {
  ActionDTO,
  ActionHistoryCardConfig,
  ActionSource,
  ActionType,
  HomeAssistant,
} from "./types.js";

const CARD_TAG = "poolman-action-history-card";

/** Hard cap on actions rendered, irrespective of ``config.limit``. */
const MAX_ACTIONS = 50;

const TYPE_ICONS: Record<ActionType, string> = {
  chemical: "🧪",
  cleaning: "🧹",
  maintenance: "🔧",
};

const TYPE_LABELS: Record<ActionType, string> = {
  chemical: "Chemical treatment",
  cleaning: "Cleaning",
  maintenance: "Maintenance",
};

const SOURCE_LABELS: Record<ActionSource, string> = {
  user: "Manual",
  recommendation: "Recommendation",
  automation: "Automation",
};

/** Format a quantity + unit pair, falling back to the missing placeholder. */
function formatQuantity(action: ActionDTO): string {
  if (action.type !== "chemical") return MISSING;
  if (!Number.isFinite(action.quantity)) return MISSING;
  const value = Number.isInteger(action.quantity)
    ? action.quantity.toString()
    : action.quantity.toFixed(1);
  return action.unit ? `${value} ${action.unit}` : value;
}

/** Return a stable identifier for the local day a timestamp falls on. */
function dayKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate(),
  ).padStart(2, "0")}`;
}

export class PoolmanActionHistoryCard extends LitElement {
  static override styles = actionHistoryStyles;

  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: ActionHistoryCardConfig;

  /** Lovelace card size hint (1 unit ≈ 50px). */
  public getCardSize(): number {
    return 4;
  }

  public static getStubConfig(
    hass?: HomeAssistant,
  ): Partial<ActionHistoryCardConfig> {
    const deviceId = firstPoolmanDeviceId(hass);
    return {
      type: `custom:${CARD_TAG}`,
      ...(deviceId ? { device_id: deviceId } : {}),
    };
  }

  public static async getConfigElement(): Promise<HTMLElement> {
    await import("./editor/poolman-action-history-card-editor.js");
    return document.createElement("poolman-action-history-card-editor");
  }

  public setConfig(config: ActionHistoryCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    if (!config.device_id && !config.entities?.action_history) {
      throw new Error(
        "poolman-action-history-card: either `device_id` or `entities.action_history` must be provided",
      );
    }
    const requested = config.limit;
    const limit =
      typeof requested === "number" && requested > 0
        ? Math.min(Math.floor(requested), MAX_ACTIONS)
        : MAX_ACTIONS;
    this._config = {
      show_source: true,
      group_by_day: true,
      ...config,
      limit,
    };
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;

    const resolved = resolveEntities(this.hass, this._config);
    const entityId = resolved.action_history;
    const entity = getEntity(this.hass, entityId);
    const actions = this._readActions(entity);

    const poolName =
      this._config.name ??
      this._deviceName(this._config.device_id) ??
      "Pool";

    return html`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="header-icon" aria-hidden="true">📋</span>
            <span>${poolName} — Action history</span>
          </div>
          ${actions.length > 0
            ? html`<span class="total">${actions.length}</span>`
            : nothing}
        </div>

        ${actions.length === 0
          ? html`<div class="empty">No actions recorded yet</div>`
          : html`<div class="timeline">${this._renderTimeline(actions)}</div>`}
      </ha-card>
    `;
  }

  private _readActions(
    entity: ReturnType<typeof getEntity>,
  ): ActionDTO[] {
    if (!entity) return [];
    const raw = entity.attributes["actions"];
    if (!Array.isArray(raw)) return [];
    const limit = this._config?.limit ?? MAX_ACTIONS;
    // Defensive copy + sort: backend returns newest-first but the card
    // must not depend on that to remain robust against attribute drift.
    return (raw as ActionDTO[])
      .filter((a) => a && typeof a.timestamp === "string")
      .slice()
      .sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1))
      .slice(0, limit);
  }

  private _renderTimeline(actions: ActionDTO[]): TemplateResult[] {
    const groupByDay = this._config?.group_by_day !== false;
    if (!groupByDay) {
      return actions.map((action) => this._renderRow(action));
    }

    const rows: TemplateResult[] = [];
    let currentDay: string | undefined;
    for (const action of actions) {
      const date = new Date(action.timestamp);
      const key = dayKey(date);
      if (key !== currentDay) {
        currentDay = key;
        rows.push(
          html`<div class="day-header">${this._formatDayHeader(date)}</div>`,
        );
      }
      rows.push(this._renderRow(action));
    }
    return rows;
  }

  private _renderRow(action: ActionDTO): TemplateResult {
    const icon = TYPE_ICONS[action.type] ?? "•";
    const typeLabel = TYPE_LABELS[action.type] ?? action.type;
    const sourceLabel = SOURCE_LABELS[action.source] ?? action.source;
    const quantity = formatQuantity(action);
    const interactive = Boolean(action.recommendation_id);
    const time = this._formatTime(new Date(action.timestamp));

    const onActivate = () => this._openAction(action);

    return html`
      <div
        class="action-row ${interactive ? "interactive" : ""}"
        data-type=${action.type}
        data-source=${action.source}
        role=${interactive ? "button" : "presentation"}
        tabindex=${interactive ? "0" : "-1"}
        @click=${interactive ? onActivate : nothing}
        @keydown=${interactive
          ? (ev: KeyboardEvent) => {
              if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                onActivate();
              }
            }
          : nothing}
      >
        <span class="action-icon" aria-hidden="true">${icon}</span>
        <div class="action-body">
          <span class="action-title">
            ${typeLabel}${action.treatment_id ? html` · ${action.treatment_id}` : nothing}
          </span>
          <span class="action-meta">
            <span class="quantity">${quantity}</span>
            ${this._config?.show_source !== false
              ? html`<span class="source-badge ${action.source}">${sourceLabel}</span>`
              : nothing}
          </span>
        </div>
        <span class="action-time">${time}</span>
      </div>
    `;
  }

  private _openAction(action: ActionDTO): void {
    // Best-effort: open more-info for the originating recommendations
    // sensor when present, otherwise fall back to the history sensor.
    const resolved = resolveEntities(this.hass!, this._config!);
    const target = resolved.recommendations ?? resolved.action_history;
    if (!target) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId: target, action_id: action.id },
      }),
    );
  }

  private _formatDayHeader(date: Date): string {
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    if (dayKey(date) === dayKey(today)) return "Today";
    if (dayKey(date) === dayKey(yesterday)) return "Yesterday";
    const language = this.hass?.locale?.language;
    try {
      return new Intl.DateTimeFormat(language, {
        weekday: "long",
        day: "2-digit",
        month: "short",
        year:
          date.getFullYear() === today.getFullYear() ? undefined : "numeric",
      }).format(date);
    } catch {
      return date.toDateString();
    }
  }

  private _formatTime(date: Date): string {
    const language = this.hass?.locale?.language;
    try {
      return new Intl.DateTimeFormat(language, {
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    } catch {
      return `${String(date.getHours()).padStart(2, "0")}:${String(
        date.getMinutes(),
      ).padStart(2, "0")}`;
    }
  }

  private _deviceName(deviceId: string | undefined): string | undefined {
    if (!deviceId || !this.hass?.devices) return undefined;
    const device = this.hass.devices[deviceId];
    if (!device) return undefined;
    return device.name_by_user ?? device.name ?? undefined;
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, PoolmanActionHistoryCard);
}
