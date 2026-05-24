---
icon: lucide/zap
---

# Quick Actions Card

The **Quick Actions** card is a first-party Lovelace custom card shipped
with the Pool Manager integration. It gives one-tap access to the most
common pool operations — trigger an analysis, boost filtration for a
short period, or record a manual treatment — by calling the existing
Pool Manager services.

```text
┌──────────────────────────────────────────────┐
│  Quick Actions                               │
│                                              │
│  [🔍 Analyze now]  [⏱ +2 h]  [⏱ +4 h]        │
│  [🧪 Record treatment]                       │
└──────────────────────────────────────────────┘
```

All buttons surface live feedback:

- a spinner while the service runs,
- a brief success flash on completion,
- an inline error message if the call fails.

## Installation

The bundled JavaScript file is **auto-registered** by the integration:
no manual Lovelace resource setup is required. The card type
`custom:poolman-quick-actions-card` becomes available as soon as the
Pool Manager integration is loaded.

If the card type does not appear in the dashboard card picker after a
restart, perform a hard refresh of the browser (Ctrl+F5) to bypass the
HTTP cache.

## Configuration

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | — | Must be `custom:poolman-quick-actions-card`. |
| `device_id` | string | — | Pool Manager device id. Required. |
| `name` | string | device name | Card title. |
| `analyze` | bool | `true` | Show the "Analyze now" button. |
| `boost` | bool | `true` | Show the filtration boost (+2h / +4h) buttons. |
| `record` | bool | `true` | Show the "Record treatment" button. |

## Examples

### Minimal

```yaml
type: custom:poolman-quick-actions-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
```

### Boost-only quick row

```yaml
type: custom:poolman-quick-actions-card
device_id: 6a1f9d52b1f04b1cb2c2c4e9a7e5d9f1
name: Boost filtration
analyze: false
record: false
```

## Service mapping

| Button | Service | Payload |
| --- | --- | --- |
| Analyze now | `poolman.analyze` | `{ device_id }` |
| +2 h | `poolman.boost_filtration` | `{ device_id, hours: 2 }` |
| +4 h | `poolman.boost_filtration` | `{ device_id, hours: 4 }` |
| Record treatment | `poolman.record_action` | `{ device_id, type, product_id?, quantity?, unit?, note? }` |

## Behavior

- **One-tap services**: every button calls the matching HA service
  immediately on tap. No business logic runs in the card.
- **Visual feedback**: each button cycles through `idle → pending →
  success → idle` (`success` shows for ~1.5 s). On a service failure,
  the button switches to an `error` state and shows the message
  returned by HA below the buttons; the state reverts after ~3 s.
- **Record treatment dialog**: opens an inline dialog with a type
  selector (`chemical`, `cleaning`, `maintenance`), optional product
  id, quantity, unit (one of `g`, `kg`, `mL`, `L`, `tablet`) and a note
  field. Empty optional fields are stripped from the service payload.
  `unit` is only sent when a `product_id` is provided.
- **Localization**: labels are rendered in English by default and
  switch to French when the active Home Assistant language is `fr*`.
- **Mobile-friendly**: the buttons use a responsive grid
  (`auto-fit minmax(140px, 1fr)`) and 48 px tap targets. Animations
  honor `prefers-reduced-motion`.
- **Graceful degradation**: if the frontend cannot call services (e.g.
  in a preview environment), the card shows a "Service calls
  unavailable" notice and disables the buttons.
