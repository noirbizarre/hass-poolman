import type {
  EntityKey,
  GlobalStatus,
  HassEntity,
  HomeAssistant,
  MetricKey,
  PoolOverviewCardConfig,
  RecommendationDTO,
} from "./types.js";

/** Placeholder rendered for any missing / unavailable metric. */
export const MISSING = "—";

const UNAVAILABLE_STATES = new Set(["unavailable", "unknown", "none", ""]);

export function isUnavailable(entity: HassEntity | undefined): boolean {
  if (!entity) return true;
  return UNAVAILABLE_STATES.has(entity.state);
}

/**
 * Build the map of `EntityKey -> entity_id` for the configured device.
 *
 * Resolution order:
 *   1. Explicit `entities:` overrides in the card config.
 *   2. Entities from the device registry whose `unique_id` suffix matches.
 *   3. Heuristic fallback by entity_id suffix (works without entity registry).
 */
export function resolveEntities(
  hass: HomeAssistant,
  config: PoolOverviewCardConfig,
): Partial<Record<EntityKey, string>> {
  const out: Partial<Record<EntityKey, string>> = { ...(config.entities ?? {}) };
  const suffixes: Record<EntityKey, string> = {
    status: "_status",
    water_quality_score: "_water_quality_score",
    recommendations: "_recommendations",
    temperature: "_temperature",
    ph: "_ph",
    free_chlorine: "_free_chlorine",
    orp: "_orp",
  };

  // Per-parameter status sensors (ph_status, orp_status, free_chlorine_status)
  // would also end with `_status`; ensure we match the *global* status only.
  const isGlobalStatus = (entityId: string): boolean => {
    return (
      entityId.endsWith("_status") &&
      !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(entityId)
    );
  };

  if (config.device_id && hass.entities) {
    for (const reg of Object.values(hass.entities)) {
      if (reg.device_id !== config.device_id) continue;
      for (const [key, suffix] of Object.entries(suffixes) as Array<
        [EntityKey, string]
      >) {
        if (out[key]) continue;
        if (key === "status") {
          if (isGlobalStatus(reg.entity_id)) out[key] = reg.entity_id;
        } else if (reg.entity_id.endsWith(suffix)) {
          out[key] = reg.entity_id;
        }
      }
    }
  }

  return out;
}

export function getEntity(
  hass: HomeAssistant,
  entityId: string | undefined,
): HassEntity | undefined {
  if (!entityId) return undefined;
  return hass.states[entityId];
}

/** Read the global pool status, normalised to one of the four known values. */
export function readStatus(entity: HassEntity | undefined): GlobalStatus {
  if (!entity || isUnavailable(entity)) return "unknown";
  const value = entity.state.toLowerCase();
  if (value === "ok" || value === "warning" || value === "critical") {
    return value;
  }
  return "unknown";
}

const STATUS_PRESENTATION: Record<
  GlobalStatus,
  { label: string; color: string; icon: string }
> = {
  ok: { label: "OK", color: "var(--success-color, #43a047)", icon: "✅" },
  warning: {
    label: "WARNING",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️",
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨",
  },
  unknown: {
    label: "UNKNOWN",
    color: "var(--disabled-text-color, #9e9e9e)",
    icon: "❔",
  },
};

export function statusPresentation(status: GlobalStatus) {
  return STATUS_PRESENTATION[status];
}

const METRIC_PRESENTATION: Record<
  MetricKey,
  { icon: string; label: string; fractionDigits: number; unitFallback: string }
> = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" },
};

export function metricPresentation(key: MetricKey) {
  return METRIC_PRESENTATION[key];
}

/** Format a numeric metric, returning MISSING if the entity is unavailable. */
export function formatMetric(
  entity: HassEntity | undefined,
  fractionDigits: number,
  unitFallback: string,
): string {
  if (isUnavailable(entity)) return MISSING;
  const raw = entity!.state;
  const num = Number(raw);
  const unit =
    (entity!.attributes["unit_of_measurement"] as string | undefined) ??
    unitFallback;
  if (Number.isFinite(num)) {
    return `${num.toFixed(fractionDigits)}${unit ? ` ${unit}` : ""}`.trim();
  }
  return `${raw}${unit ? ` ${unit}` : ""}`.trim();
}

/** Determine the default metric set, swapping in ORP when chlorine is missing. */
export function effectiveMetrics(
  config: PoolOverviewCardConfig,
  resolved: Partial<Record<EntityKey, string>>,
  hass: HomeAssistant,
): MetricKey[] {
  if (config.metrics?.length) return config.metrics;
  const base: MetricKey[] = ["temperature", "ph", "free_chlorine"];
  const cl = getEntity(hass, resolved.free_chlorine);
  if (isUnavailable(cl) && resolved.orp && !isUnavailable(getEntity(hass, resolved.orp))) {
    return ["temperature", "ph", "orp"];
  }
  return base;
}

/** Quality score severity bucket (matches gauge thresholds 80/50/0). */
export function scoreSeverity(score: number): "good" | "warn" | "bad" {
  if (score >= 80) return "good";
  if (score >= 50) return "warn";
  return "bad";
}

export function readRecommendations(
  entity: HassEntity | undefined,
): { count: number; list: RecommendationDTO[] } {
  if (!entity) return { count: 0, list: [] };
  const count = Number(entity.state);
  const list = (entity.attributes["recommendations"] as RecommendationDTO[] | undefined) ?? [];
  return { count: Number.isFinite(count) ? count : list.length, list };
}
