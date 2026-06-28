---
icon: lucide/gauge
---

# Entities

Pool Manager creates a device for each configured pool, with the following
entities attached to it. All entity IDs follow the pattern
`{domain}.{pool_name}_{key}`, where `{pool_name}` is derived from the pool
name you set during configuration.

## Sensors

The integration always creates the following sensors. Additional sensors are
created conditionally: `filtration_boost_remaining` when a pump entity is
configured, and one `inventory_product` sensor per tracked inventory product.

### Reading sensors

These sensors mirror your source sensor values, giving you a unified view under the Pool Manager device.

| Entity | Name | Unit | Device Class | Description |
| --- | --- | --- | --- | --- |
| `sensor.{pool}_temperature` | Water temperature | °C | `temperature` | Water temperature reading |
| `sensor.{pool}_ph` | pH | -- | `ph` | pH level reading |
| `sensor.{pool}_orp` | ORP | mV | -- | Oxidation-Reduction Potential reading |
| `sensor.{pool}_free_chlorine` | Free chlorine | ppm | -- | Free chlorine level reading |
| `sensor.{pool}_ec` | Electrical conductivity | µS/cm | -- | Electrical conductivity reading (diagnostic/trending) |
| `sensor.{pool}_tds` | Total dissolved solids | ppm | -- | TDS reading (computed from EC or manual measurement) |
| `sensor.{pool}_salt` | Salt level | ppm | -- | Salt level reading (salt electrolysis pools) |

### Computed sensors

These sensors are calculated by Pool Manager from your readings.

| Entity | Name | Unit | Description |
| --- | --- | --- | --- |
| `sensor.{pool}_filtration_duration` | Recommended filtration | h | Recommended daily filtration hours, computed from water temperature, filter type efficiency, outdoor temperature, and pump capacity. See [Pool Modes](pool-modes.md#filtration) for the full algorithm. |
| `sensor.{pool}_water_quality_score` | Water quality | % | Overall water quality score from 0 (poor) to 100 (perfect). See [Water Chemistry](water-chemistry.md#water-quality-score) for scoring details. |
| `sensor.{pool}_recommendations` | Recommendations | -- | Number of active recommendations. See details below. |
| `sensor.{pool}_problems` | Problems | -- | Number of detected water-quality problems. See details below. |
| `sensor.{pool}_chemistry_actions` | Chemistry actions | -- | Number of chemistry-related actions (excludes filtration). See details below. |
| `sensor.{pool}_active_treatments` | Active treatments | -- | Number of currently active chemical treatments. See [Chemistry Tracking](chemistry-tracking.md) for details. |
| `sensor.{pool}_safe_at` | Safe to swim at | -- | Timestamp (`timestamp` device class) indicating when the pool will be safe for swimming after treatments. `None` if already safe. |
| `sensor.{pool}_status` | Pool status | -- | Overall pool status (`enum` device class), one of `ok`, `warning`, `critical`, derived from detected problems. See details below. |
| `sensor.{pool}_action_history` | Last action | -- | Timestamp (`timestamp` device class) of the most recently recorded action. See [Action History Card](action-history-card.md) for the exposed history. |

### Recommendations sensor attributes

The `recommendations` sensor exposes additional detail through its state attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `actions` | list of strings | Human-readable description of each active recommendation (e.g., `"Add 450g of ph_minus"`) |
| `critical_count` | integer | Number of critical priority recommendations |

These attributes can be used in automations, templates, or Lovelace cards to display detailed recommendation information.

### Problems sensor attributes

The `problems` sensor exposes the raw, severity-ordered list of detected
water-quality problems through its state attributes. The state itself is the
problem count (`0` when the pool is healthy).

| Attribute | Type | Description |
| --- | --- | --- |
| `problems` | list of objects | One entry per detected problem, ordered by severity (most severe first). |
| `worst_severity` | string | Highest severity present, one of `ok`, `low`, `medium`, `critical`. `ok` when the list is empty. |

Each entry in `problems` has the following shape:

| Field | Type | Description |
| --- | --- | --- |
| `code` | string | Machine-readable identifier, e.g. `"ph_too_high"`. |
| `severity` | string | One of `low`, `medium`, `critical`. |
| `metric` | string or null | The chemistry metric affected (`ph`, `orp`, `chlorine`, ...) or `null`. |
| `value` | float or null | The measured value that triggered the problem. |
| `expected_range` | list of two floats or null | `[minimum, maximum]` acceptable range. |
| `message` | string | Human-readable description of the problem. |

### Pool status sensor attributes

The `status` sensor summarizes the overall pool health as a single
`ok` / `warning` / `critical` value, derived from the detected problems.
Its state attributes are:

| Attribute | Type | Description |
| --- | --- | --- |
| `problem_count` | integer | Total number of detected problems |
| `critical_count` | integer | Number of problems with `critical` severity |
| `worst_severity` | string | Highest severity present, one of `ok`, `low`, `medium`, `critical` |

### Chemistry actions sensor attributes

The `chemistry_actions` sensor exposes chemistry-related recommendations
(chemical treatments and alerts, excluding filtration) through its
state attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `actions` | list of objects | Each action includes `kind` (suggestion/requirement), `message`, `product`, `quantity_g`, `spoon_count`, and `spoon_name` |
| `suggestion_count` | integer | Number of actions classified as suggestions |
| `requirement_count` | integer | Number of actions classified as requirements |

When [measuring spoon sizes](getting-started.md#step-3-measuring-spoons) are
configured, each action object also includes:

| Field | Type | Description |
| --- | --- | --- |
| `spoon_count` | integer or null | Number of spoons equivalent to the gram dosage (null for tablet products or when no spoons are configured) |
| `spoon_name` | string or null | Name of the selected spoon size (null when spoon_count is null) |

See [Spoon Equivalents](water-chemistry.md#spoon-equivalents) for details on
how spoon counts are calculated.

Actions are classified as either **suggestions** (optional improvements)
or **requirements** (needed to keep the pool safe).
See [Action Kind](rules-and-recommendations.md#action-kind) for details.

### Chemistry status sensors

These sensors provide a quick **good / warning / bad** status for each chemistry
parameter. See [Water Chemistry -- Chemistry Status](water-chemistry.md#chemistry-status)
for how the status is determined.

| Entity | Name | Options | Description |
| --- | --- | --- | --- |
| `sensor.{pool}_ph_status` | pH status | `good`, `warning`, `bad` | pH level status |
| `sensor.{pool}_orp_status` | ORP status | `good`, `warning`, `bad` | Oxidation-Reduction Potential status |
| `sensor.{pool}_free_chlorine_status` | Free chlorine status | `good`, `warning`, `bad` | Free chlorine level status |
| `sensor.{pool}_salt_status` | Salt status | `good`, `warning`, `bad` | Salt level status (salt electrolysis pools) |
| `sensor.{pool}_tac_status` | TAC status | `good`, `warning`, `bad` | Total alkalinity status |
| `sensor.{pool}_cya_status` | CYA status | `good`, `warning`, `bad` | Cyanuric acid (stabilizer) status |
| `sensor.{pool}_hardness_status` | Hardness status | `good`, `warning`, `bad` | Calcium hardness status |
| `sensor.{pool}_tds_status` | TDS status | `good`, `warning`, `bad` | Total dissolved solids status |

Each status sensor exposes additional detail through its state attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `value` | float | Current reading for this parameter |
| `target` | float | Ideal target value |
| `minimum` | float | Lower bound of the acceptable range |
| `maximum` | float | Upper bound of the acceptable range |
| `score` | integer | Individual quality score from 0 (poor) to 100 (perfect) |

!!! tip "Dashboard ideas"

    Use the status sensors to build a chemistry dashboard card that shows
    at a glance which parameters need attention. Combine with the extra
    attributes to display the actual reading alongside its target range.

### Active treatments sensor attributes

The `active_treatments` sensor exposes additional detail through its state attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `treatments` | list of objects | Details of each active treatment: `product`, `applied_at`, `safe_at`, `quantity_g` |

### Activation step sensor

The `activation_step` sensor tracks progress through the
[Activation Wizard](pool-modes.md#activation-wizard). It shows the next
pending step when the pool is in **Activating** mode, or has no state
when the pool is in any other mode.

| Entity | Name | Device Class | Options | Description |
| --- | --- | --- | --- | --- |
| `sensor.{pool}_activation_step` | Activation step | `enum` | `remove_cover`, `raise_water_level`, `clean_pool_and_filter`, `shock_treatment`, `intensive_filtration` | Current (next pending) activation wizard step |

#### Activation step sensor attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `completed_steps` | list of strings | Steps already confirmed |
| `pending_steps` | list of strings | Steps still to be confirmed |
| `progress` | string | Progress in the format `"N/5"` (e.g. `"2/5"`) |
| `started_at` | string (ISO 8601) | When the activation process was started |

These attributes are empty when the pool is not in activating mode.
The checklist state persists across Home Assistant restarts via the
`RestoreEntity` mechanism.

## Binary Sensors

The integration always creates 3 binary sensor entities for quick status checks,
plus one `inventory_low_stock` binary sensor per inventory product that has a
low-stock threshold configured:

| Entity | Name | Device Class | ON when... |
| --- | --- | --- | --- |
| `binary_sensor.{pool}_water_ok` | Water quality | `safety` | No high or critical priority recommendations exist **and** no active treatment safety period is in effect |
| `binary_sensor.{pool}_action_required` | Action required | `problem` | At least one recommendation is active (any priority) |
| `binary_sensor.{pool}_swimming_safe` | Swimming safe | `safety` | No active treatment safety period is in effect (all swim wait times have elapsed) |
| `binary_sensor.{pool}_{product}_low_stock` | `{product}` low stock | `problem` | The tracked product's stock falls at or below its configured low-stock threshold. See [Inventory](inventory.md). |

!!! tip "Automation ideas"

    Use `binary_sensor.{pool}_action_required` to trigger notifications when your pool needs attention, `binary_sensor.{pool}_water_ok` to confirm that water chemistry is within acceptable ranges, or `binary_sensor.{pool}_swimming_safe` to notify when the pool is safe for swimming after a treatment.

## Event Entities

The integration creates one event entity per chemical product (18 total)
to track treatment applications. Each entity fires an `applied` event
when a treatment is recorded via the `poolman.add_treatment` service.

Treatment-specific products (e.g., `bromine_tablet`) are disabled by
default when the pool's configured treatment type doesn't match.
Universal products (e.g., `ph_minus`, `flocculant`) are always enabled.

See [Chemistry Tracking](chemistry-tracking.md) for the full list of products, safety profiles, and usage details.

In addition, the integration creates 10 measurement event entities, one per
measurable parameter, that fire a `measured` event when a manual measurement is
recorded via the `poolman.record_measure` service:

| Entity | Name | Event types |
| --- | --- | --- |
| `event.{pool}_measure_ph` | pH measured | `measured` |
| `event.{pool}_measure_orp` | ORP measured | `measured` |
| `event.{pool}_measure_free_chlorine` | Free chlorine measured | `measured` |
| `event.{pool}_measure_ec` | EC measured | `measured` |
| `event.{pool}_measure_tds` | TDS measured | `measured` |
| `event.{pool}_measure_tac` | TAC measured | `measured` |
| `event.{pool}_measure_cya` | CYA measured | `measured` |
| `event.{pool}_measure_hardness` | Hardness measured | `measured` |
| `event.{pool}_measure_salt` | Salt measured | `measured` |
| `event.{pool}_measure_temperature` | Temperature measured | `measured` |

A `filtration` event entity is also created when a pump entity is configured
(see [Filtration Control Entities](#filtration-control-entities) below).

## Select

The integration creates select entities to control operational settings:

| Entity | Name | Options | Default | Description |
| --- | --- | --- | --- | --- |
| `select.{pool}_mode` | Pool mode | `active`, `hibernating`, `winter_active`, `winter_passive`, `activating` | `active` | Controls the current operational mode. Persisted across restarts. See [Pool Modes](pool-modes.md) for details on each mode. |

Changing the mode immediately triggers a data refresh and recalculation of all computed values.

## Filtration Control Entities

When a **pump switch entity** is configured in the integration, additional
entities are created for automatic pump scheduling. These entities are
**conditional** -- they only appear when a pump entity is set.

See [Filtration Control](filtration-control.md) for full details on
scheduling behavior, cross-midnight support, and automation examples.

### Switch

| Entity | Name | Description |
| --- | --- | --- |
| `switch.{pool}_filtration_control` | Filtration control | Enables or disables automatic daily pump scheduling. Turning off immediately stops the pump. |

### Duration Mode Select

| Entity | Name | Default | Options | Description |
| --- | --- | --- | --- | --- |
| `select.{pool}_filtration_duration_mode` | Filtration duration mode | Dynamic | `manual`, `dynamic`, `split_static`, `split_dynamic` | Controls how filtration duration is determined and whether it is split across two periods. See [Filtration Control -- Duration Mode](filtration-control.md#duration-mode). |

### Time

| Entity | Name | Default | Availability | Description |
| --- | --- | --- | --- | --- |
| `time.{pool}_filtration_start_time` | Filtration start time | 10:00 | Always | Daily start time for the first filtration period |
| `time.{pool}_filtration_start_time_2` | Filtration start time 2 | 16:00 | Split modes only | Start time for the second filtration period |

### Number

| Entity | Name | Default | Range | Availability | Description |
| --- | --- | --- | --- | --- | --- |
| `number.{pool}_filtration_duration_setting` | Filtration duration | 8 h | 1--24 h (step 0.5) | Always | Duration of the first filtration period. In dynamic mode, automatically updated to match the recommendation. |
| `number.{pool}_filtration_duration_setting_2` | Filtration duration 2 | 4 h | 0--24 h (step 0.5) | Split modes only | Duration of the second filtration period. In split (dynamic) mode, auto-computed from the recommendation. |

### Event

| Entity | Name | Event types | Description |
| --- | --- | --- | --- |
| `event.{pool}_filtration` | Filtration | `filtration_started`, `filtration_stopped`, `boost_started`, `boost_consumed`, `boost_cancelled` | Fires when the pump is turned on or off by the scheduler, or when a boost is activated, consumed, or cancelled |

### Filtration Boost

| Entity | Name | Type | Options / Unit | Description |
| --- | --- | --- | --- | --- |
| `select.{pool}_filtration_boost` | Filtration boost | Select | `none`, `+2h`, `+4h`, `+8h`, `+24h` | Activate a preset boost or cancel the current boost |
| `sensor.{pool}_filtration_boost_remaining` | Filtration boost remaining | Sensor | hours | Remaining boost hours (0 when no boost is active) |

See [Filtration Control -- Filtration Boost](filtration-control.md#filtration-boost)
for full details on boost behavior, persistence, and automation examples.

## Events

Pool Manager fires `poolman_event` events on the Home Assistant event bus
whenever a status transition is detected between two consecutive data updates.
These events can be used to trigger automations (e.g. send a notification when
pH becomes bad).

!!! note

    Events are **not** fired on the first data update after Home Assistant
    starts, since there is no previous state to compare against.

### Chemistry status changed

Fired when an individual chemistry parameter transitions between `good`,
`warning`, and `bad`, or becomes available/unavailable.

| Field | Type | Description |
| --- | --- | --- |
| `device_id` | string | Device registry ID of the pool device |
| `type` | string | `chemistry_status_changed` |
| `parameter` | string | `ph`, `orp`, `free_chlorine`, `salt`, `tac`, `cya`, `hardness`, or `tds` |
| `previous_status` | string \| null | Previous status (`good`, `warning`, `bad`), or null if the parameter was unavailable |
| `status` | string \| null | New status (`good`, `warning`, `bad`), or null if the parameter became unavailable |

### Water status changed

Fired when the overall water quality flips between OK and not OK (based on
whether high/critical recommendations exist).

| Field | Type | Description |
| --- | --- | --- |
| `device_id` | string | Device registry ID of the pool device |
| `type` | string | `water_status_changed` |
| `parameter` | string | `water` |
| `previous_status` | string | `ok` or `not_ok` |
| `status` | string | `ok` or `not_ok` |

!!! tip "Automation example"

    ```yaml
    automation:
      - alias: "Notify when pH goes bad"
        trigger:
          - platform: event
            event_type: poolman_event
            event_data:
              type: chemistry_status_changed
              parameter: ph
              status: bad
        action:
          - service: notify.mobile_app
            data:
              title: "Pool Alert"
              message: "pH has gone out of range!"
    ```
