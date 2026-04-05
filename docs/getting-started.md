---
icon: lucide/rocket
---
<!-- markdownlint-disable MD024 -->

# Getting Started

## Prerequisites

Pool Manager aggregates readings from **existing Home Assistant sensor
entities**. You need at least the following sensors already configured
in your Home Assistant instance:

### Required sensors

| Sensor | Unit | Description |
| --- | --- | --- |
| Water temperature | °C | Pool water temperature |
| pH | -- | pH level (0--14 scale) |
| ORP | mV | Oxidation-Reduction Potential |

### Optional sensors

These sensors enable additional recommendations and improve the water quality score accuracy:

| Sensor | Unit | Description |
| --- | --- | --- |
| Free Chlorine | ppm | Free chlorine level (supplements ORP) |
| EC (Electrical Conductivity) | µS/cm | Conductivity level (diagnostic/trending) |
| Salt | ppm | Salt level (for salt electrolysis pools) |
| TAC (Total Alkalinity) | ppm | Alkalinity level |
| CYA (Cyanuric Acid) | ppm | Stabilizer level |
| Calcium Hardness | ppm | Water hardness |
| Outdoor temperature | °C | Ambient / air temperature (improves filtration recommendation) |

### Optional actuators

| Entity | Type | Description |
| --- | --- | --- |
| Pump switch | switch | Pump on/off entity. Enables [filtration control](filtration-control.md) (automatic daily pump scheduling). |

### Compatible sensor sources

Your sensors can come from any source:

- **Dedicated pool probes**: Flipr, iopool, Sutro, Blue Connect, etc.
- **DIY sensors**: ESPHome, Tasmota, or any MQTT-based sensor
- **Manual input**: Home Assistant input_number helpers for manual readings

## Installation

### HACS (recommended)

<!-- markdownlint-disable MD033 MD013 -->

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=noirbizarre&repository=hass-poolman&category=Integration)

<!-- markdownlint-enable MD033 MD013 -->

Or manually add as a custom repository:

1. Open [HACS](https://hacs.xyz/) in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu and select **Custom repositories**
4. Add `noirbizarre/hass-poolman` with category **Integration**
5. Search for and install **Pool Manager**
6. Restart Home Assistant

### Manual installation

1. Download the [latest release](https://github.com/noirbizarre/hass-poolman/releases/latest)
2. Copy the `custom_components/poolman` directory into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

<!-- markdownlint-disable MD013 -->
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=poolman)
<!-- markdownlint-enable MD013 -->

Or go to **Settings > Devices & Services > Add Integration** and search for **Pool Manager**.

The integration is configured through a four-step UI flow. No YAML configuration is needed.

### Step 1: Pool basics

The first step collects your pool's physical characteristics.

#### Required parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| Pool name | text | My Pool | Name for your pool (used as device name and unique identifier) |
| Volume | number (m³) | 50.0 | Pool water volume (1--500 m³) |
| Shape | select | Rectangular | Pool shape: Rectangular, Round, or Freeform |

### Step 2: Chemistry

The second step configures your water treatment method and chemistry sensor entities.

#### Required parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| Treatment type | select | Chlorine | Water treatment method: Chlorine, Salt electrolysis, Bromine, or Active oxygen |
| pH entity | entity (sensor) | -- | pH sensor entity |
| ORP entity | entity (sensor) | -- | ORP sensor entity |

The treatment type determines which sanitizer products are recommended by the
[rule engine](rules-and-recommendations.md#sanitizer-rule-orp). For example,
a chlorine-treated pool will receive chlorine tablet recommendations, while a
bromine-treated pool will receive bromine tablet recommendations.

#### Optional parameters

| Parameter | Type | Description |
| --- | --- | --- |
| Free chlorine entity | entity (sensor) | Free chlorine sensor (supplements ORP for sanitizer evaluation) |
| EC entity | entity (sensor) | Electrical conductivity sensor (diagnostic, no scoring) |
| Salt entity | entity (sensor) | Salt level sensor (for salt electrolysis pools) |
| TAC entity | entity (sensor) | Total Alkalinity sensor |
| CYA entity | entity (sensor) | Cyanuric Acid / Stabilizer sensor |
| Hardness entity | entity (sensor) | Calcium Hardness sensor |
| TDS conversion factor | number | Factor to convert EC to TDS (default 0.5, range 0.4--0.8) |

### Step 3: Measuring spoons

The third step lets you configure up to three named measuring spoon sizes.
When spoon sizes are defined, dosage recommendations will include an
approximate number of spoons alongside the gram-based quantity
(see [Spoon Equivalents](water-chemistry.md#spoon-equivalents)).

This step is entirely optional -- you can skip it by submitting the form
without filling in any spoon names.

#### Optional parameters (up to 3 pairs)

| Parameter | Type | Description |
| --- | --- | --- |
| Spoon name | text | Label for the spoon (e.g. "Small", "Large", "Tablespoon") |
| Spoon size | number (mL) | Volume of the spoon in milliliters |

Only pairs where both the name is non-empty and the size is greater than
zero are saved.

!!! tip "Common spoon sizes"

    | Spoon | Approximate volume |
    | --- | --- |
    | Teaspoon | 5 mL |
    | Dessertspoon | 10 mL |
    | Tablespoon | 15 mL |
    | Pool scoop (small) | 25 mL |
    | Pool scoop (large) | 50 mL |

### Step 4: Filtration

The fourth step configures your filtration system.

#### Required parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| Filtration type | select | Sand | Filter type: Sand, Cartridge, Diatomaceous Earth, or Glass |
| Pump flow rate | number (m³/h) | 10.0 | Pump flow rate (1--50 m³/h) |
| Temperature entity | entity (sensor) | -- | Water temperature sensor entity |

#### Optional parameters

| Parameter | Type | Description |
| --- | --- | --- |
| Pump entity | entity (switch) | Pump switch for [filtration control](filtration-control.md) (automatic daily scheduling) |
| Outdoor temperature entity | entity (sensor) | Outdoor / air temperature sensor for heat stress adjustment |
| Weather entity | entity (weather) | Weather integration entity (used as fallback for outdoor temperature) |

!!! tip "Outdoor temperature sources"

    You can configure an outdoor temperature sensor, a weather entity, or both.
    When both are provided, the dedicated sensor takes priority. The weather
    entity's `temperature` attribute is used as a fallback.
    See [Pool Modes](pool-modes.md#step-3-outdoor-temperature-heat-stress)
    for how outdoor temperature affects filtration duration.

!!! note "Multiple pools"

    You can add the integration multiple times to manage several pools.
    Each pool is identified by its name, which must be unique.

## Reconfiguring settings

After initial setup, you can modify your chemistry and filtration settings at any time
through the integration's options:

1. Go to **Settings > Devices & Services**
2. Find **Pool Manager** and click **Configure**
3. Update the treatment type, chemistry sensors, spoon sizes, filtration type,
   pump flow rate, temperature sensor, outdoor temperature sensor, weather entity,
   or pump entity

Changes take effect immediately -- the integration reloads automatically.

## Update interval

Pool Manager reads your sensor entities and recomputes all analytics every
**5 minutes**. This interval is fixed and not configurable. Since all
computation is local, this has negligible impact on system performance.
