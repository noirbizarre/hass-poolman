---
icon: lucide/pump
---

# Filtration Control

When a **pump switch entity** is configured in the integration, Pool Manager
can automatically control your pool pump on a daily schedule. This feature
creates additional entities that let you enable scheduling, set a start time,
and configure a duration -- the pump then turns on and off automatically
every day.

## Prerequisites

Filtration control requires a **switch entity** that controls your pool pump.
This can be:

- A smart plug or relay connected via any integration (Shelly, Sonoff, Tasmota, etc.)
- An ESPHome GPIO switch
- A virtual switch for testing

Configure the pump entity in the integration's filtration settings step
(or update it later via **Settings > Devices & Services > Pool Manager > Configure**).

!!! note
    All filtration control entities are **conditional**: they are only created
    when a pump entity is configured. If you remove the pump entity from the
    configuration, these entities will no longer appear.

## Entities

When a pump entity is configured, the following entities are added to your
Pool Manager device:

### Switch

| Entity | Name | Description |
| --- | --- | --- |
| `switch.{pool}_filtration_control` | Filtration control | Enables or disables automatic daily pump scheduling |

When turned **on**, the scheduler activates and the pump follows the configured
schedule. When turned **off**, the pump is turned off **immediately** and all
scheduled triggers are cancelled.

### Select

| Entity | Name | Default | Options | Description |
| --- | --- | --- | --- | --- |
| `select.{pool}_filtration_duration_mode` | Filtration duration mode | Dynamic | `manual`, `dynamic`, `split_static`, `split_dynamic` | Controls how the filtration duration is determined and whether it is split across two periods |

See [Duration Mode](#duration-mode) below for details.

### Time

| Entity | Name | Default | Availability | Description |
| --- | --- | --- | --- | --- |
| `time.{pool}_filtration_start_time` | Filtration start time | 10:00 | Always | Daily start time for the first filtration period |
| `time.{pool}_filtration_start_time_2` | Filtration start time 2 | 16:00 | Split modes only | Start time for the second filtration period |

### Number

| Entity | Name | Default | Range | Step | Availability | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `number.{pool}_filtration_duration_setting` | Filtration duration | 8 h | 1--24 h | 0.5 h | Always | Duration of the first filtration period |
| `number.{pool}_filtration_duration_setting_2` | Filtration duration 2 | 4 h | 0--24 h | 0.5 h | Split modes only | Duration of the second filtration period |

### Event

| Entity | Name | Event types | Description |
| --- | --- | --- | --- |
| `event.{pool}_filtration` | Filtration | `filtration_started`, `filtration_stopped` | Fires when the pump is turned on or off by the scheduler |

Each event carries the following attributes:

| Attribute | Type | Example | Description |
| --- | --- | --- | --- |
| `start_time` | string (ISO time) | `"10:00:00"` | Start time of the period that triggered the event |
| `duration_hours` | float | `8.0` | Duration in hours of the triggering period |
| `end_time` | string (ISO time) | `"18:00:00"` | Computed end time of the triggering period |
| `period_index` | integer | `0` | Zero-based index of the period (0 = first, 1 = second) |

## Duration Mode

The **Filtration duration mode** select entity controls how the daily
filtration duration is determined. The default mode is **dynamic**.

There are four modes, organised into two categories: **single-period**
modes (one continuous filtration window per day) and **split** modes
(two separate filtration windows per day).

### Single-period modes

#### Dynamic mode (default)

In dynamic mode, Pool Manager automatically sets the filtration duration
from the computed recommended value on each data refresh (every 5 minutes).
The recommendation is based on water temperature, filter type efficiency,
outdoor heat stress, and pump turnover rate
(see [Pool Modes](pool-modes.md#filtration) for the full algorithm).

When the coordinator updates:

1. The recommended filtration hours are computed from current sensor readings
2. If a valid recommendation is available, the scheduler duration is
   automatically updated to match
3. The filtration duration number entity reflects the active duration

If the water temperature sensor becomes unavailable, the scheduler keeps the
last known duration until a new reading is available.

#### Manual mode

In manual mode, the computed recommendation is **not** applied to the
scheduler. The user controls the duration entirely through the filtration
duration number entity. The recommended filtration sensor
(`sensor.{pool}_filtration_duration`) still displays the computed value
for reference, but it has no effect on the schedule.

### Split modes

Split modes divide the daily filtration into **two separate periods**, each
with its own start time and duration. This is useful when you want to
distribute pump runtime across the day (e.g. morning and afternoon) rather
than running a single long filtration cycle.

When a split mode is selected:

- The **period 2 entities** (`time.{pool}_filtration_start_time_2` and
  `number.{pool}_filtration_duration_setting_2`) become available
- The scheduler manages two independent start/stop trigger pairs
- Filtration events include a `period_index` attribute (0 or 1) to identify
  which period triggered the event

!!! note
    Period 2 entities are always **created** when a pump is configured, but
    they report as **unavailable** unless a split mode is active. This means
    you never need to reload the integration when switching between single
    and split modes.

#### Split (static) mode

Both periods use **user-set durations**. You configure a start time and
duration for each period independently through the time and number
entities.

| Period | Start time entity | Duration entity |
| --- | --- | --- |
| Period 1 | `time.{pool}_filtration_start_time` | `number.{pool}_filtration_duration_setting` |
| Period 2 | `time.{pool}_filtration_start_time_2` | `number.{pool}_filtration_duration_setting_2` |

The recommended filtration sensor still displays the computed value for
reference, but neither period is automatically adjusted.

#### Split (dynamic) mode

The first period has a **user-set duration**, while the second period's
duration is **automatically computed** to reach the daily filtration
recommendation. On each coordinator update:

1. The recommended total filtration hours are computed
2. The second period's duration is set to:
   `max(min_dynamic_duration, recommendation − period_1_duration)`
3. If the recommendation is less than or equal to the first period's
   duration, the second period effectively has zero duration (or
   the configured minimum)

This mode is ideal when you want a guaranteed base filtration in the
morning and an adaptive top-up in the afternoon based on current
conditions.

The `filtration_duration_setting_2` number entity reflects the
auto-computed duration. It is available but adjustments are overwritten
on the next coordinator refresh.

### Switching modes

- **Dynamic to manual**: The scheduler keeps the last dynamically computed
  duration. The user can then adjust it via the number entity.
- **Manual to dynamic**: The next coordinator update (within 5 minutes)
  syncs the scheduler to the current recommendation.
- **Single to split**: Period 2 entities become available with their
  default values (start 16:00, duration 4 h). A second set of
  start/stop triggers is registered in the scheduler.
- **Split to single**: Period 2 entities become unavailable. The second
  period's triggers are removed from the scheduler.

The selected mode is persisted across Home Assistant restarts.

## Scheduling Behavior

### Daily cycle

The scheduler registers time-based triggers for the start and end of each
filtration period. In single-period modes, one start/stop pair is
registered. In split modes, two independent start/stop pairs are managed.

Each period operates independently: the pump turns on at the period's
start time and off after its duration elapses.

### Cross-midnight schedules

Schedules that cross midnight are fully supported for any period.
For example, a start time of **22:00** with a duration of **8 hours**
creates a window from 22:00 to 06:00 the next day.

### Restart recovery

Both the filtration control switch state and all time/duration settings are
persisted across Home Assistant restarts using `RestoreEntity`. On restart:

1. The switch restores its last known on/off state
2. The time, duration, and duration mode entities restore their last values
   (including period 2 entities in split modes)
3. If the switch was on, the scheduler re-enables and checks whether the
   current time falls within any active window -- if so, the pump is turned
   on immediately
4. If the restored mode is dynamic or split (dynamic), the first coordinator
   refresh syncs the scheduler duration(s) from the current recommendation

### Mid-cycle changes

Changing the start time or duration while the scheduler is enabled takes
effect **immediately**:

- Triggers are recalculated for the new schedule
- The pump state is adjusted right away: if the current time is now inside
  the new window the pump turns on; if outside, it turns off

### Disabling filtration control

Turning off the filtration control switch:

1. Cancels all scheduled triggers
2. Turns the pump **off immediately**

## Automation Examples

### Notify when filtration starts

```yaml
automation:
  - alias: "Notify filtration started"
    trigger:
      - platform: state
        entity_id: event.demo_pool_filtration
        attribute: event_type
        to: "filtration_started"
    action:
      - action: notify.notify
        data:
          title: "Pool"
          message: "Filtration pump started"
```

## Relationship to the Recommended Filtration Sensor

The `sensor.{pool}_filtration_duration` entity is an **advisory** value
computed from water temperature, filter type, outdoor temperature, and pump
capacity (see [Pool Modes](pool-modes.md#filtration) for the algorithm).

The filtration control feature provides **active control**: it actually
turns the pump on and off.

- In **dynamic mode** (the default), the recommendation feeds directly
  into the scheduler on each coordinator refresh.
- In **manual mode**, the recommendation has no effect on the schedule.
- In **split (static) mode**, the recommendation is displayed for
  reference only; both periods are fully user-controlled.
- In **split (dynamic) mode**, the recommendation drives the second
  period's duration: the remaining hours after subtracting period 1's
  duration are assigned to period 2.
