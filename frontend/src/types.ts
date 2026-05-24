// Minimal subset of the Home Assistant frontend types used by the cards.
// We intentionally avoid pulling the upstream `home-assistant-js-websocket`
// types to keep the bundle self-contained and the build hermetic.

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed?: string;
  last_updated?: string;
}

export interface HassDeviceRegistryEntry {
  id: string;
  name: string | null;
  name_by_user: string | null;
  identifiers?: Array<[string, string]>;
}

export interface HassEntityRegistryEntry {
  entity_id: string;
  device_id: string | null;
  unique_id: string;
  platform: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities?: Record<string, HassEntityRegistryEntry>;
  devices?: Record<string, HassDeviceRegistryEntry>;
  callService?: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ) => Promise<unknown>;
  formatEntityState?: (entity: HassEntity) => string;
  locale?: { language: string };
}

export interface PoolOverviewCardConfig {
  type: string;
  device_id?: string;
  name?: string;
  metrics?: MetricKey[];
  show_score?: boolean;
  recommendations_path?: string;
  entities?: Partial<Record<EntityKey, string>>;
}

export type MetricKey = "temperature" | "ph" | "free_chlorine" | "orp";

export type EntityKey =
  | "status"
  | "water_quality_score"
  | "recommendations"
  | "problems"
  | MetricKey;

/**
 * Metric identifier emitted by the backend `Problem.metric` field. Mirrors
 * the canonical `MetricName` enum in
 * `custom_components/poolman/domain/problem.py`.
 */
export type ProblemMetric =
  | "ph"
  | "orp"
  | "chlorine"
  | "temperature"
  | "cya"
  | "alkalinity"
  | "hardness"
  | "tds"
  | "salt"
  | "ec";

/** Per-problem severity emitted by the backend (StrEnum value). */
export type ProblemSeverity = "low" | "medium" | "critical";

/** Sensor-level aggregate severity; `"ok"` when the problem list is empty. */
export type WorstSeverity = ProblemSeverity | "ok";

/** Problem payload as serialized by the `problems` sensor attribute. */
export interface ProblemDTO {
  code: string;
  severity: ProblemSeverity;
  metric: ProblemMetric | null;
  value: number | null;
  expected_range: [number, number] | null;
  message: string;
}

export interface PoolProblemCardConfig {
  type: string;
  device_id?: string;
  name?: string;
  entity?: string;
  /** Maximum number of problem rows to render before showing a "+N more" hint. */
  max?: number;
}

/** When to prompt the user before calling `poolman.apply_recommendation`. */
export type ConfirmApplyMode = "never" | "always" | "critical_high";

export interface PoolRecommendationsCardConfig {
  type: string;
  /** Pool Manager device id. Used to resolve the recommendations sensor and
   *  passed to `poolman.apply_recommendation`. Required unless `entity` is set. */
  device_id?: string;
  /** Optional override for the recommendations sensor entity id. */
  entity?: string;
  /** Card title override. Defaults to the device name. */
  name?: string;
  /** Show the priority text in the badge in addition to the color. Default true. */
  show_severity?: boolean;
  /** Confirmation policy for the Apply button. Default `critical_high`. */
  confirm_apply?: ConfirmApplyMode;
}

export interface RecommendationTreatment {
  id?: string;
  product_id: string;
  name: string;
  quantity: number;
  unit: string;
  /** Optional wait duration in seconds. */
  duration?: number | null;
}

/** Legacy alias kept for backwards compat with consumers of the overview card. */
export type RecommendationAction = RecommendationTreatment;

export type RecommendationSeverity = "low" | "medium" | "critical";
export type RecommendationPriority = "low" | "medium" | "high" | "critical";
export type RecommendationKind = "suggestion" | "requirement";

export interface RecommendationDTO {
  id: string;
  type: string;
  severity: RecommendationSeverity;
  priority?: RecommendationPriority;
  kind?: RecommendationKind;
  title: string;
  description?: string;
  reason?: string;
  /** Modern contract emitted by the backend. */
  treatments?: RecommendationTreatment[];
  /** Legacy field name retained for older payloads. */
  actions?: RecommendationTreatment[];
  related_metrics?: string[];
}

export type GlobalStatus = "ok" | "warning" | "critical" | "unknown";

declare global {
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description: string;
      preview?: boolean;
      documentationURL?: string;
    }>;
  }
}
