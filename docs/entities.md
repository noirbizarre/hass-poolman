---
icon: lucide/gauge
---

# Entities

Pool Manager creates a device for each configured pool, with the following
entities attached to it. All entity IDs follow the pattern
`{domain}.{pool_name}_{key}`, where `{pool_name}` is derived from the pool
name you set during configuration.

## Sensors

The integration creates 6 sensor entities:

### Reading sensors

These sensors mirror your source sensor values, giving you a unified view under the Pool Manager device.

| Entity | Name | Unit | Device Class | Description |
| --- | --- | --- | --- | --- |
| `sensor.{pool}_temperature` | Water temperature | °C | `temperature` | Water temperature reading |
| `sensor.{pool}_ph` | pH | -- | `ph` | pH level reading |
| `sensor.{pool}_orp` | ORP | mV | -- | Oxidation-Reduction Potential reading |

### Computed sensors

These sensors are calculated by Pool Manager from your readings.

| Entity | Name | Unit | Description |
| --- | --- | --- | --- |
| `sensor.{pool}_filtration_duration` | Recommended filtration | h | Recommended daily filtration hours, computed from water temperature, filter type efficiency, outdoor temperature, and pump capacity. See [Pool Modes](pool-modes.md#filtration) for the full algorithm. |
| `sensor.{pool}_water_quality_score` | Water quality | % | Overall water quality score from 0 (poor) to 100 (perfect). See [Water Chemistry](water-chemistry.md#water-quality-score) for scoring details. |
| `sensor.{pool}_recommendations` | Recommendations | -- | Number of active recommendations. See details below. |

### Recommendations sensor attributes

The `recommendations` sensor exposes additional detail through its state attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `actions` | list of strings | Human-readable description of each active recommendation (e.g., `"Add 450g of ph_minus"`) |
| `critical_count` | integer | Number of high or critical priority recommendations |

These attributes can be used in automations, templates, or Lovelace cards to display detailed recommendation information.

## Binary Sensors

The integration creates 2 binary sensor entities for quick status checks:

| Entity | Name | Device Class | ON when... |
| --- | --- | --- | --- |
| `binary_sensor.{pool}_water_ok` | Water quality | `safety` | No high or critical priority recommendations exist |
| `binary_sensor.{pool}_action_required` | Action required | `problem` | At least one recommendation is active (any priority) |

!!! tip "Automation ideas"

    Use `binary_sensor.{pool}_action_required` to trigger notifications when your pool needs attention, or `binary_sensor.{pool}_water_ok` to confirm that water chemistry is within acceptable ranges.

## Select

The integration creates 1 select entity to control the operational mode:

| Entity | Name | Options | Description |
| --- | --- | --- | --- |
| `select.{pool}_mode` | Pool mode | `running`, `winter_active`, `winter_passive` | Controls the current operational mode. See [Pool Modes](pool-modes.md) for details on each mode. |

Changing the mode immediately triggers a data refresh and recalculation of all computed values.
