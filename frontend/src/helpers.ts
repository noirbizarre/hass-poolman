import type {
  ActionHistoryCardConfig,
  EntityKey,
  GlobalStatus,
  HassEntity,
  HomeAssistant,
  MetricKey,
  PoolOverviewCardConfig,
  PoolRecommendationsCardConfig,
  ProblemDTO,
  ProblemMetric,
  ProblemSeverity,
  RecommendationDTO,
  RecommendationPriority,
  RecommendationTreatment,
  WorstSeverity,
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
  config: PoolOverviewCardConfig | ActionHistoryCardConfig,
): Partial<Record<EntityKey, string>> {
  const out: Partial<Record<EntityKey, string>> = {
    ...((config.entities as Partial<Record<EntityKey, string>> | undefined) ?? {}),
  };
  const suffixes: Record<EntityKey, string> = {
    status: "_status",
    water_quality_score: "_water_quality_score",
    recommendations: "_recommendations",
    problems: "_problems",
    action_history: "_action_history",
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

/** Severity ranking matching the backend ordering in `sensor.py`. */
const SEVERITY_RANK: Record<ProblemSeverity, number> = {
  low: 1,
  medium: 2,
  critical: 3,
};

const SEVERITY_PRESENTATION: Record<
  ProblemSeverity,
  { label: string; color: string; icon: string }
> = {
  low: {
    label: "INFO",
    color: "var(--info-color, #2196f3)",
    icon: "ℹ️",
  },
  medium: {
    label: "WARNING",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️",
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨",
  },
};

export function severityPresentation(severity: ProblemSeverity) {
  return SEVERITY_PRESENTATION[severity];
}

export function severityRank(severity: ProblemSeverity): number {
  return SEVERITY_RANK[severity];
}

/** Per-metric formatting hints. Keys match {@link ProblemMetric}. */
export const PROBLEM_METRIC_FORMAT: Record<
  ProblemMetric,
  { unit: string; fractionDigits: number; label: string }
> = {
  ph: { unit: "", fractionDigits: 2, label: "pH" },
  orp: { unit: "mV", fractionDigits: 0, label: "ORP" },
  chlorine: { unit: "mg/L", fractionDigits: 1, label: "Chlorine" },
  temperature: { unit: "°C", fractionDigits: 1, label: "Temperature" },
  cya: { unit: "mg/L", fractionDigits: 0, label: "CYA" },
  alkalinity: { unit: "mg/L", fractionDigits: 0, label: "Alkalinity" },
  hardness: { unit: "mg/L", fractionDigits: 0, label: "Hardness" },
  tds: { unit: "mg/L", fractionDigits: 0, label: "TDS" },
  salt: { unit: "g/L", fractionDigits: 2, label: "Salt" },
  ec: { unit: "µS/cm", fractionDigits: 0, label: "EC" },
};

function appendUnit(value: string, unit: string): string {
  return unit ? `${value} ${unit}` : value;
}

/** Format a numeric problem value using the per-metric map. */
export function formatProblemValue(
  metric: ProblemMetric | null,
  value: number | null,
): string {
  if (value === null || !Number.isFinite(value)) return MISSING;
  if (metric === null) return String(value);
  const meta = PROBLEM_METRIC_FORMAT[metric];
  if (!meta) return String(value);
  return appendUnit(value.toFixed(meta.fractionDigits), meta.unit);
}

/** Format an `[min, max]` expected range using the per-metric map. */
export function formatExpectedRange(
  metric: ProblemMetric | null,
  range: [number, number] | null,
): string {
  if (!range || range.length !== 2) return MISSING;
  const [min, max] = range;
  if (!Number.isFinite(min) || !Number.isFinite(max)) return MISSING;
  if (metric === null) return `${min}–${max}`;
  const meta = PROBLEM_METRIC_FORMAT[metric];
  if (!meta) return `${min}–${max}`;
  const minStr = min.toFixed(meta.fractionDigits);
  const maxStr = max.toFixed(meta.fractionDigits);
  return appendUnit(`${minStr}–${maxStr}`, meta.unit);
}

/** Resolve a metric's human-friendly label, falling back to the raw key. */
export function problemMetricLabel(metric: ProblemMetric | null): string {
  if (metric === null) return "";
  return PROBLEM_METRIC_FORMAT[metric]?.label ?? metric;
}

/**
 * Read the `problems` sensor: count, attribute list and worst severity.
 *
 * Defensive against missing / unavailable entities; falls back to a healthy
 * zero state so the card renders the empty placeholder rather than nothing.
 */
export function readProblems(entity: HassEntity | undefined): {
  count: number;
  list: ProblemDTO[];
  worst: WorstSeverity;
} {
  if (!entity || isUnavailable(entity)) {
    return { count: 0, list: [], worst: "ok" };
  }
  const list =
    (entity.attributes["problems"] as ProblemDTO[] | undefined) ?? [];
  const rawCount = Number(entity.state);
  const count = Number.isFinite(rawCount) ? rawCount : list.length;
  const worstAttr = entity.attributes["worst_severity"] as
    | WorstSeverity
    | undefined;
  const worst: WorstSeverity =
    worstAttr ?? (list[0]?.severity ?? "ok");
  return { count, list, worst };
}

/** Read the treatments list from a recommendation, accepting both the
 *  modern `treatments` field and the legacy `actions` alias. */
export function recommendationTreatments(
  rec: RecommendationDTO,
): RecommendationTreatment[] {
  return rec.treatments ?? rec.actions ?? [];
}

const PRIORITY_PRESENTATION: Record<
  RecommendationPriority,
  { label: string; color: string; icon: string }
> = {
  low: {
    label: "LOW",
    color: "var(--info-color, #2196f3)",
    icon: "ℹ️",
  },
  medium: {
    label: "MEDIUM",
    color: "var(--warning-color, #fbc02d)",
    icon: "⚠️",
  },
  high: {
    label: "HIGH",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️",
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨",
  },
};

/** Resolve the effective priority for a recommendation.
 *
 *  Priority is the canonical field; severity is used as a fallback for
 *  legacy payloads that omit `priority`. Severity values map to priority
 *  as follows: `low → low`, `medium → medium`, `critical → critical`.
 */
export function recommendationPriority(
  rec: Pick<RecommendationDTO, "priority" | "severity">,
): RecommendationPriority {
  if (rec.priority) return rec.priority;
  switch (rec.severity) {
    case "critical":
      return "critical";
    case "medium":
      return "medium";
    default:
      return "low";
  }
}

/** Map a recommendation's priority (or severity fallback) to a label, color
 *  and icon used by the recommendations card. */
export function priorityPresentation(
  rec: Pick<RecommendationDTO, "priority" | "severity">,
): { label: string; color: string; icon: string; key: RecommendationPriority } {
  const key = recommendationPriority(rec);
  return { key, ...PRIORITY_PRESENTATION[key] };
}

/** Format a treatment line: "200 g · pH-" with the locale-aware quantity. */
export function formatTreatment(
  treatment: RecommendationTreatment,
  locale?: string,
): string {
  const lang = locale ?? "en";
  const qty = Number.isFinite(treatment.quantity)
    ? treatment.quantity.toLocaleString(lang, { maximumFractionDigits: 2 })
    : String(treatment.quantity ?? "");
  const unit = treatment.unit ?? "";
  const amount = qty ? `${qty}${unit ? ` ${unit}` : ""}` : unit;
  return amount ? `${amount} · ${treatment.name}` : treatment.name;
}

/** Resolve the recommendations sensor entity id from a card config. */
export function resolveRecommendationsEntity(
  hass: HomeAssistant,
  config: PoolRecommendationsCardConfig,
): string | undefined {
  if (config.entity) return config.entity;
  if (!config.device_id || !hass.entities) return undefined;
  for (const reg of Object.values(hass.entities)) {
    if (reg.device_id !== config.device_id) continue;
    if (reg.entity_id.endsWith("_recommendations")) return reg.entity_id;
  }
  return undefined;
}
