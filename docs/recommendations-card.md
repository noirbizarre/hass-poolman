---
icon: lucide/list-checks
---

# Recommendations Card

The **Recommendations** card is a first-party Lovelace custom card shipped
with the Pool Manager integration. It renders the active recommendations
produced by the rule engine as an actionable list, with one-tap apply and
ignore buttons backed by the
[`poolman.apply_recommendation`](rules-and-recommendations.md#poolmanapply_recommendation)
service.

```text
┌──────────────────────────────────────────┐
│  📋 My Pool                       2 / 2  │
│                                          │
│  ┃ 🚨 CRITICAL  Shock pool         ›    │
│  ┃   ORP is critically low               │
│  ┃                 [ Ignore ] [ Apply ]  │
│                                          │
│  ┃ ⚠️ MEDIUM    Lower pH           ›    │
│  ┃   pH is above the safe range          │
│  ┃                 [ Ignore ] [ Apply ]  │
└──────────────────────────────────────────┘
```

## Installation

The bundled JavaScript file is **auto-registered** by the integration:
no manual Lovelace resource setup is required. The card type
`custom:poolman-recommendations-card` becomes available as soon as the
Pool Manager integration is loaded.

If the card type does not appear in the dashboard card picker after a
restart, perform a hard refresh of the browser (Ctrl+F5) to bypass the
HTTP cache.

## Configuration

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | -- | Must be `custom:poolman-recommendations-card`. |
| `device_id` | string | -- | Pool Manager device id. Resolves the recommendations sensor automatically and is passed to `poolman.apply_recommendation`. Required unless `entity` is provided. |
| `entity` | string | -- | Explicit recommendations sensor entity id override. When set, `device_id` becomes optional but is still required for the `Apply` button to work. |
| `name` | string | device name | Card title. |
| `show_severity` | bool | `true` | Show the priority label in the badge (in addition to the colour). |
| `confirm_apply` | string | `critical_high` | When to prompt before calling the apply service. One of `never`, `always`, `critical_high`. |

## Examples

### Minimal

```yaml
type: custom:poolman-recommendations-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

### Always confirm before applying

```yaml
type: custom:poolman-recommendations-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
confirm_apply: always
```

### Explicit entity override

```yaml
type: custom:poolman-recommendations-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
entity: sensor.backyard_pool_recommendations
name: Backyard Pool — Recommendations
```

### Side-by-side with the overview card

```yaml
type: vertical-stack
cards:
  - type: custom:poolman-pool-overview-card
    device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
  - type: custom:poolman-recommendations-card
    device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

## Behavior

- **Priority colors**: `low` -> blue, `medium` -> amber, `high` -> orange,
  `critical` -> red. The priority is read from the `priority` field of
  each recommendation; when it is missing (legacy payloads), the
  `severity` field is used as a fallback.
- **Expandable details**: click the row header to reveal the
  recommendation `reason`, the ordered list of treatments
  (product / quantity / unit) and the related metric chips.
- **Apply**: calls
  [`poolman.apply_recommendation`](rules-and-recommendations.md#poolmanapply_recommendation)
  with `device_id` and the recommendation `id`. The service creates one
  `Action` per treatment, decrements inventory and fires
  `poolman_action_recorded`.
- **Confirmation**: by default a native `confirm()` prompt is shown
  before applying `critical` or `high` priority recommendations. The
  `confirm_apply` option lets you opt into `always` or `never`.
- **Ignore**: dismisses the recommendation for the current card instance
  only. No service is called, no event is fired and no state is
  persisted across reloads. If the backend re-emits the same
  recommendation id after it has disappeared once, it becomes visible
  again automatically.
- **Empty state**: when no recommendations are active (or all visible
  recommendations have been dismissed), the card shows the message
  "Your pool is in good condition".
- **Graceful degradation**: if the recommendations sensor is missing or
  reports `unavailable`/`unknown`, the card renders a
  "Recommendations unavailable" placeholder instead of crashing.
- **Mobile-friendly**: the action buttons stretch to full width below
  ~360 px so they remain easy to tap.

## See also

- [Pool Overview Card](pool-overview-card.md) -- the glanceable summary
  card. Its recommendation count row links back to this card via the
  `recommendations_path` option.
- [Rules & Recommendations](rules-and-recommendations.md) -- how
  recommendations are produced and what each priority level means.
