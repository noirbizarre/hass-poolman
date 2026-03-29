---
icon: lucide/flask-conical
---

# Chemistry Tracking

Pool Manager lets you record chemical treatments applied to your pool and
automatically tracks safety wait times. The system uses Home Assistant event
entities as storage, so all treatment history appears in HA's logbook and
history views without any external database.

## How It Works

1. **Record a treatment** using the `poolman.add_treatment` service (from an
   automation, the Developer Tools, or a Lovelace button).
2. The corresponding **event entity** fires an `applied` event with timestamp,
   quantity, and optional notes.
3. The coordinator reads each event entity's last application time on every
   refresh cycle (every 5 minutes) and computes:
   - Which treatments are still **active** (product is still working).
   - Whether the pool is **safe for swimming** (all safety wait times elapsed).
   - **When** the pool will next be safe (`safe_at` timestamp).
4. Derived sensors and binary sensors update automatically.

## The `add_treatment` Service

```yaml
service: poolman.add_treatment
target:
  device_id: <your_pool_device_id>
data:
  product: chlore_choc
  quantity_g: 500
  notes: "Shock treatment after heavy rain"
```

| Field | Required | Description |
| --- | --- | --- |
| `product` | Yes | Chemical product identifier (see table below) |
| `quantity_g` | No | Amount of product used in grams |
| `notes` | No | Free-text note about the treatment |

The service can be targeted at a specific pool device or called without a
target to apply to all configured pools.

## Chemical Products

Pool Manager supports 18 chemical products. Each product has an **activity
duration** (how long it remains active after application) and a **swim wait
time** (how long to wait before swimming).

### Treatment-specific products

These products are enabled by default only when the pool's configured
treatment type matches.

| Product | Activity (h) | Swim Wait (h) | Enabled for |
| --- | :---: | :---: | --- |
| `chlore_choc` -- Shock chlorine | 48 | 24 | Chlorine, Salt electrolysis |
| `galet_chlore` -- Chlorine tablet | 0 | 0 | Chlorine |
| `salt` -- Salt | 24 | 24 | Salt electrolysis |
| `bromine_tablet` -- Bromine tablet | 0 | 0 | Bromine |
| `bromine_shock` -- Bromine shock | 48 | 24 | Bromine |
| `active_oxygen_tablet` -- Active oxygen tablet | 0 | 0 | Active oxygen |
| `active_oxygen_activator` -- Active oxygen activator | 48 | 24 | Active oxygen |

### Universal products

These products are always enabled regardless of treatment type.

| Product | Activity (h) | Swim Wait (h) |
| --- | :---: | :---: |
| `ph_minus` -- pH minus | 6 | 6 |
| `ph_plus` -- pH plus | 6 | 6 |
| `neutralizer` -- Neutralizer | 4 | 4 |
| `tac_plus` -- Alkalinity increaser | 6 | 6 |
| `flocculant` -- Flocculant | 48 | 24 |
| `anti_algae` -- Anti-algae | 24 | 24 |
| `stabilizer` -- Stabilizer (CYA) | 24 | 24 |
| `clarifier` -- Clarifier | 0 | 0 |
| `metal_sequestrant` -- Metal sequestrant | 0 | 0 |
| `calcium_hardness_increaser` -- Calcium hardness increaser | 6 | 6 |
| `winterizing_product` -- Winterizing product | 0 | 0 |

Products with **0 / 0** for activity and swim wait are continuous-release or
swimming-compatible products that do not impose any safety restriction.

## Entities Created

### Event entities (18)

One event entity per chemical product. Each entity:

- Fires an `applied` event type when the product is used.
- Persists its last event across HA restarts via `RestoreEntity`.
- Appears in HA's logbook with timestamp and event data.

### Sensors

| Entity | Description |
| --- | --- |
| `sensor.{pool}_active_treatments` | Number of currently active treatments. Extra attributes contain a `treatments` list with `product`, `applied_at`, `safe_at`, and `quantity_g` for each active treatment. |
| `sensor.{pool}_safe_at` | Timestamp of when the pool will be safe for swimming. `None` if already safe. |

### Binary sensors

| Entity | Description |
| --- | --- |
| `binary_sensor.{pool}_swimming_safe` | `True` when all treatment safety periods have elapsed. |

The existing `binary_sensor.{pool}_water_ok` also considers swimming safety:
it is `False` when either water chemistry is bad **or** a treatment safety
period is active.

## Automation Examples

### Notify when pool is safe after treatment

```yaml
automation:
  - alias: "Notify pool safe after treatment"
    trigger:
      - platform: state
        entity_id: binary_sensor.pool_swimming_safe
        to: "on"
    action:
      - action: notify.mobile_app
        data:
          title: "Pool is safe"
          message: "All treatment safety periods have elapsed. You can swim!"
```

### Record treatment from a Lovelace button

```yaml
type: button
name: Shock treatment
tap_action:
  action: perform-action
  perform_action: poolman.add_treatment
  target:
    device_id: <your_pool_device_id>
  data:
    product: chlore_choc
    quantity_g: 500
```
