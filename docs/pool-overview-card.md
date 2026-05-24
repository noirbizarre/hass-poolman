---
icon: lucide/layout-dashboard
---

# Pool Overview Card

The **Pool Overview** card is a first-party Lovelace custom card shipped
with the Pool Manager integration. It renders a single, glanceable
summary of one pool — the equivalent of the ioPool home screen — using
the sensors already produced by the integration.

```text
┌──────────────────────────────────────┐
│  🏊 My Pool                ● WARNING │
│                                      │
│  🌡️ 26.0 °C  pH 7.8  Cl 0.8 mg/L     │
│  Quality score: 72 / 100             │
│                                      │
│  ⚠️  2 recommendations             › │
└──────────────────────────────────────┘
```

## Installation

The bundled JavaScript file is **auto-registered** by the integration:
no manual Lovelace resource setup is required. The card type
`custom:poolman-pool-overview-card` becomes available as soon as the
Pool Manager integration is loaded.

If the card type does not appear in the dashboard card picker after a
restart, perform a hard refresh of the browser (Ctrl+F5) to bypass the
HTTP cache.

## Configuration

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | — | Must be `custom:poolman-pool-overview-card`. |
| `device_id` | string | — | Pool Manager device id. Resolves all entities automatically. Required unless `entities:` is provided. |
| `name` | string | device name | Card title. |
| `metrics` | list | `[temperature, ph, free_chlorine]` (auto-swaps in `orp` when free chlorine is missing) | Metric tiles to display, in order. Allowed: `temperature`, `ph`, `free_chlorine`, `orp`. |
| `show_score` | bool | `true` | Show the water-quality-score row. |
| `recommendations_path` | string | — | When set, tapping the recommendations row navigates to this path instead of opening the more-info dialog. |
| `entities` | map | — | Explicit per-key overrides: `status`, `water_quality_score`, `recommendations`, `temperature`, `ph`, `free_chlorine`, `orp`. |

## Examples

### Minimal

```yaml
type: custom:poolman-pool-overview-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

### Explicit entities (no device registry lookup)

```yaml
type: custom:poolman-pool-overview-card
name: Backyard Pool
entities:
  status: sensor.backyard_pool_status
  water_quality_score: sensor.backyard_pool_water_quality_score
  recommendations: sensor.backyard_pool_recommendations
  temperature: sensor.backyard_pool_temperature
  ph: sensor.backyard_pool_ph
  free_chlorine: sensor.backyard_pool_free_chlorine
```

### Link recommendations to a dedicated view

```yaml
type: custom:poolman-pool-overview-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
recommendations_path: /lovelace/pool-recommendations
```

## Behavior

- **Status badge** colors: `ok` → green, `warning` → orange,
  `critical` → red, anything else → grey "UNKNOWN".
- **Missing or unavailable** entities render as `—`; the card never
  crashes when a sensor is absent.
- **Mobile-friendly**: the metric grid uses
  `auto-fit minmax(100px, 1fr)` and reflows on narrow viewports.
- **Auto-update**: the card re-renders when any of the consumed entity
  states change.
- **Empty recommendations**: when the recommendation count is zero, the
  row shows "Your pool is in good condition" and tap is disabled.

## See also

- [Recommendations Card](recommendations-card.md) -- the actionable list
  view paired with this overview card. Set `recommendations_path` here
  to navigate users straight to the dashboard view that hosts it.
