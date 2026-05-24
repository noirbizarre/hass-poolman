---
icon: lucide/history
---

# Action History Card

The **Action History** card is a first-party Lovelace custom card shipped
with the Pool Manager integration. It renders a chronological timeline
of recorded pool actions — chemical treatments, cleaning, maintenance —
so users can verify recent interventions and trace problems back to a
specific operation.

```text
┌──────────────────────────────────────────────────────────────┐
│  📋 My Pool — Action history                              5  │
│                                                              │
│  TODAY                                                       │
│  🧪  Chemical treatment · ph_minus_300g  150 g [USER]  14:30 │
│                                                              │
│  YESTERDAY                                                   │
│  🧹  Cleaning · vacuum_pool        — [MANUAL]          09:00 │
│  🔧  Maintenance · backwash        — [MANUAL]          08:00 │
└──────────────────────────────────────────────────────────────┘
```

## Installation

The bundled JavaScript file is **auto-registered** by the integration:
no manual Lovelace resource setup is required. The card type
`custom:poolman-action-history-card` becomes available as soon as the
Pool Manager integration is loaded.

If the card type does not appear in the dashboard card picker after a
restart, perform a hard refresh of the browser (Ctrl+F5) to bypass the
HTTP cache.

## Data source

The card consumes the `sensor.<pool>_action_history` entity created by
the integration:

- **State** — ISO-8601 timestamp of the most recently recorded action
  (`timestamp` device class), or `unknown` when no action has ever been
  recorded.
- **Attributes**
    - `actions` — list of the last 50 recorded actions, newest first.
    - `limit` — the server-side cap (`50`).
    - `total` — total number of actions ever recorded.

Each action exposes: `id`, `type`, `source`, `treatment_id`, `quantity`,
`unit`, `timestamp` (ISO-8601), `recommendation_id`, `product_id` and
`duration` (seconds, or `null`).

## Configuration

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | — | Must be `custom:poolman-action-history-card`. |
| `device_id` | string | — | Pool Manager device id. Resolves the action history entity automatically. Required unless `entities.action_history` is provided. |
| `name` | string | device name | Card title prefix. |
| `limit` | int | `50` | Maximum number of actions rendered (clamped to `50`). |
| `show_source` | bool | `true` | Show the source badge (`MANUAL` / `RECOMMENDATION` / `AUTOMATION`). |
| `group_by_day` | bool | `true` | Group rows under day headers (`Today`, `Yesterday`, or a localized date). |
| `entities.action_history` | string | — | Explicit override for the action history entity id. |

## Examples

### Minimal

```yaml
type: custom:poolman-action-history-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

### Limit to the 10 most recent actions, flat list

```yaml
type: custom:poolman-action-history-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
limit: 10
group_by_day: false
```

### Explicit entity (no device registry lookup)

```yaml
type: custom:poolman-action-history-card
name: Backyard Pool
entities:
  action_history: sensor.backyard_pool_action_history
```

## Behavior

- Rows are rendered in **reverse chronological order** (most recent
  first). The card defensively re-sorts on the client side.
- **Icons by type**: chemical → 🧪, cleaning → 🧹, maintenance → 🔧.
- **Quantity + unit** is rendered for chemical actions only; other
  types show `—`.
- **Source badge** colors: `user` → green, `recommendation` → orange,
  `automation` → blue.
- Tapping an action that originated from a recommendation opens the
  associated more-info dialog (or the action history sensor as a
  fallback).
- Empty state: when the action log is empty, the card shows
  "No actions recorded yet".
- **Mobile-friendly**: the row layout reflows on narrow viewports, with
  the timestamp moving below the action body.
