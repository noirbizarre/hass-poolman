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

### Time

| Entity | Name | Default | Description |
| --- | --- | --- | --- |
| `time.{pool}_filtration_start_time` | Filtration start time | 10:00 | Daily start time for the filtration cycle |

### Number

| Entity | Name | Default | Range | Step | Description |
| --- | --- | --- | --- | --- | --- |
| `number.{pool}_filtration_duration_setting` | Filtration duration | 8 h | 1--24 h | 0.5 h | Duration of each daily filtration cycle |

### Event

| Entity | Name | Event types | Description |
| --- | --- | --- | --- |
| `event.{pool}_filtration` | Filtration | `filtration_started`, `filtration_stopped` | Fires when the pump is turned on or off by the scheduler |

Each event carries the following attributes:

| Attribute | Type | Example | Description |
| --- | --- | --- | --- |
| `start_time` | string (ISO time) | `"10:00:00"` | Configured start time |
| `duration_hours` | float | `8.0` | Configured duration in hours |
| `end_time` | string (ISO time) | `"18:00:00"` | Computed end time |

## Scheduling Behavior

### Daily cycle

The scheduler registers time-based triggers for the start and end of each
daily filtration window. At the configured start time, the pump turns on.
After the configured duration elapses, the pump turns off.

### Cross-midnight schedules

Schedules that cross midnight are fully supported. For example, a start time
of **22:00** with a duration of **8 hours** creates a window from 22:00 to
06:00 the next day.

### Restart recovery

Both the filtration control switch state and the time/duration settings are
persisted across Home Assistant restarts using `RestoreEntity`. On restart:

1. The switch restores its last known on/off state
2. The time and duration entities restore their last values
3. If the switch was on, the scheduler re-enables and checks whether the
   current time falls within the active window -- if so, the pump is turned
   on immediately

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

### Adjust duration based on recommended filtration

You can use the recommended filtration sensor to automatically adjust
the filtration duration setting:

```yaml
automation:
  - alias: "Sync filtration duration with recommendation"
    trigger:
      - platform: state
        entity_id: sensor.demo_pool_filtration_duration
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.demo_pool_filtration_duration
            state: "unavailable"
    action:
      - action: number.set_value
        target:
          entity_id: number.demo_pool_filtration_duration_setting
        data:
          value: "{{ states('sensor.demo_pool_filtration_duration') | float }}"
```

## Relationship to the Recommended Filtration Sensor

The `sensor.{pool}_filtration_duration` entity is an **advisory** value
computed from water temperature, filter type, outdoor temperature, and pump
capacity (see [Pool Modes](pool-modes.md#filtration) for the algorithm).

The filtration control feature provides **active control**: it actually
turns the pump on and off. The two work independently -- the recommended
duration does not automatically set the control duration. You can connect
them via automation (see example above) or set the duration manually.
