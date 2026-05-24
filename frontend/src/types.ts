// Minimal subset of the Home Assistant frontend types used by the card.
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
  | MetricKey;

export interface RecommendationAction {
  product_id: string;
  name: string;
  quantity: number;
  unit: string;
}

export interface RecommendationDTO {
  id: string;
  type: string;
  severity: "info" | "warning" | "critical";
  title: string;
  description?: string;
  reason?: string;
  actions?: RecommendationAction[];
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
