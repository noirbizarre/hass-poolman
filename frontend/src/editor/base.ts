// Shared utilities for the Poolman Lovelace visual card editors.
//
// All editors render an HA-native `<ha-form>` element fed with a selector
// schema. This module centralises the bits each editor needs: the
// integration domain used by the device selector, the `config-changed` event
// helper, and a `computeLabel` factory backed by `i18n.ts`.

import { t, type TranslationKey } from "../i18n.js";

/** Integration slug used to filter the HA device picker to Pool Manager. */
export const POOLMAN_INTEGRATION = "poolman";

/** Schema entry shape accepted by HA's `<ha-form>` element. */
export interface SchemaItem {
  name: string;
  required?: boolean;
  selector?: Record<string, unknown>;
  default?: unknown;
}

/** Dispatch the standard HA `config-changed` event with the merged config. */
export function fireConfigChanged(target: EventTarget, config: unknown): void {
  target.dispatchEvent(
    new CustomEvent("config-changed", {
      detail: { config },
      bubbles: true,
      composed: true,
    }),
  );
}

/**
 * Build a `computeLabel` function for `<ha-form>` that translates schema entry
 * names (and select-option values) through `i18n.ts`.
 *
 * The convention is: schema entry `name` is the config field name (`device_id`,
 * `metrics`, …). We map it to a `editor_*` translation key, falling back to
 * the schema name itself when no translation exists.
 */
export function makeComputeLabel(
  lang: string | undefined,
): (schema: SchemaItem) => string {
  return (schema: SchemaItem) => {
    const key = schemaLabelKey(schema.name);
    if (!key) return schema.name;
    return t(lang, key);
  };
}

/** Map a schema entry name to its translation key. */
function schemaLabelKey(name: string): TranslationKey | undefined {
  switch (name) {
    case "device_id":
      return "editor_device";
    case "entity":
      return "editor_entity";
    case "name":
      return "editor_name";
    case "metrics":
      return "editor_metrics";
    case "show_score":
      return "editor_show_score";
    case "recommendations_path":
      return "editor_recommendations_path";
    case "max":
      return "editor_max";
    case "show_severity":
      return "editor_show_severity";
    case "confirm_apply":
      return "editor_confirm_apply";
    case "limit":
      return "editor_limit";
    case "show_source":
      return "editor_show_source";
    case "group_by_day":
      return "editor_group_by_day";
    case "analyze":
      return "editor_analyze";
    case "boost":
      return "editor_boost";
    case "record":
      return "editor_record";
    default:
      return undefined;
  }
}

/** Selector entry for a Pool Manager device picker (integration-filtered). */
export const deviceSelector = {
  device: { integration: POOLMAN_INTEGRATION },
} as const;

/** Selector for a sensor entity (used as fallback when no device is set). */
export function entitySelector(
  domain: string | string[] = "sensor",
): Record<string, unknown> {
  return { entity: { domain } };
}

/** Boolean selector. */
export const boolSelector = { boolean: {} } as const;

/** Free-text selector. */
export const textSelector = { text: {} } as const;

/** Bounded number selector. */
export function numberSelector(
  min: number,
  max: number,
  step = 1,
): Record<string, unknown> {
  return { number: { min, max, step, mode: "box" } };
}

/**
 * Pick the first Pool Manager device id available on the given `hass`,
 * filtered by integration when the entity registry exposes that information.
 *
 * Falls back to the first registered device when no entity-registry info
 * is available (older HA frontends), which mirrors the current behaviour of
 * `poolman-quick-actions-card.getStubConfig`.
 */
export function firstPoolmanDeviceId(
  hass:
    | {
        devices?: Record<string, { id: string }>;
        entities?: Record<string, { device_id: string | null; platform: string }>;
      }
    | undefined,
): string | undefined {
  if (!hass?.devices) return undefined;
  if (hass.entities) {
    for (const entry of Object.values(hass.entities)) {
      if (entry.platform === POOLMAN_INTEGRATION && entry.device_id) {
        if (hass.devices[entry.device_id]) return entry.device_id;
      }
    }
  }
  return Object.keys(hass.devices)[0];
}
