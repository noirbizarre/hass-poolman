---
icon: lucide/stethoscope
---

# Pool Problems Card

The **Pool Problems** card is a first-party Lovelace custom card shipped
with the Pool Manager integration. It surfaces the current diagnostic
problems for one pool — what is wrong and by how much — as a
severity-ordered list. It complements the Pool Overview card, which only
shows a high-level status badge and recommendation count.

```text
┌──────────────────────────────────────────┐
│  🩺 My Pool                  ● CRITICAL  │
│                                          │
│  🚨 CRITICAL  pH is too high             │
│               pH • Current: 7.90         │
│                    Expected: 7.20–7.60   │
│                                          │
│  ⚠️ WARNING   Chlorine is too low        │
│               Chlorine • Current: 0.3 mg/L│
│                    Expected: 1.0–3.0 mg/L│
└──────────────────────────────────────────┘
```

## Installation

The bundled JavaScript file is **auto-registered** by the integration:
no manual Lovelace resource setup is required. The card type
`custom:poolman-problem-card` becomes available as soon as the
Pool Manager integration is loaded.

If the card type does not appear in the dashboard card picker after a
restart, perform a hard refresh of the browser (Ctrl+F5) to bypass the
HTTP cache.

## Configuration

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | — | Must be `custom:poolman-problem-card`. |
| `device_id` | string | — | Pool Manager device id. Resolves the `*_problems` sensor automatically. Required unless `entity` is provided. |
| `entity` | string | — | Explicit `sensor.*_problems` entity id (overrides device lookup). |
| `name` | string | device name | Card title. Falls back to `"Pool Problems"` when neither name nor device name is available. |
| `max` | integer | unlimited | Maximum number of rows to render. Excess problems are summarized as `+N more`. |

## Examples

### Minimal

```yaml
type: custom:poolman-problem-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

### Explicit entity, capped to 3 rows

```yaml
type: custom:poolman-problem-card
name: Backyard Pool
entity: sensor.backyard_pool_problems
max: 3
```

## Behavior

- **Severity ordering** is taken as-is from the
  `sensor.*_problems` attribute (already sorted by the integration).
- **Severity colors**: `critical` → red, `medium` → orange (rendered as
  WARNING), `low` → blue (rendered as INFO). The header badge reflects
  `worst_severity`; it shows a green OK badge when the pool is healthy.
- **Empty state**: when the problem count is zero the card renders
  "No problems detected — pool is healthy".
- **Unavailable**: if the entity is missing or unavailable the card
  renders an "entity unavailable" hint instead of crashing.
- **Numeric metrics**: when the problem payload includes
  `metric`, `value` and `expected_range`, the card formats both with
  the metric's natural unit (mg/L, °C, mV, …). Otherwise only
  the human-readable `message` is rendered.
- **Mobile-friendly**: each problem row collapses to a single column on
  narrow viewports.
- **Auto-update**: the card re-renders whenever the problems entity
  state changes.
