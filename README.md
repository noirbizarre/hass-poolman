<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD041 -->
<p align="center">
  <img src="custom_components/poolman/brand/logo.svg" alt="Pool Manager logo" />
</p>
<p align="center">
  A virtual pool management advisor for Home Assistant.
</p>
<p align="center">
  <img src="https://img.shields.io/github/license/noirbizarre/hass-poolman?style=default&color=0080ff" alt="License">
  <img src="https://img.shields.io/github/v/release/noirbizarre/hass-poolman" alt="Release">
  <img src="https://img.shields.io/github/last-commit/noirbizarre/hass-poolman?style=default&color=0080ff" alt="Last Commit">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS">
  </a>
</p>

---

# Pool Manager for Home Assistant

**Pool Manager** is a Home Assistant custom integration that aggregates readings from your existing sensor entities
(pH, ORP, temperature, etc.) and turns them into actionable pool management insights.
It computes recommended filtration duration, a water quality score, and chemical dosage recommendations,
all locally, with no cloud service or specific hardware required.

## Features

- **Computed analytics**: recommended daily filtration duration and a 0-100% water quality score
- **Rule engine**: actionable recommendations with chemical product and dosage
- **3 operational modes**: Running, Active Wintering, and Passive Wintering, each with adapted rules and filtration logic
- **No external dependency**: works entirely from existing Home Assistant entities, no cloud API or dedicated hardware needed
- **Multi-language**: English and French translations included

## Entities

### Sensors

| Entity | Name | Unit | Description |
| --- | --- | --- | --- |
| `sensor.{pool}_temperature` | Water temperature | °C | Water temperature reading |
| `sensor.{pool}_ph` | pH | -- | pH level reading |
| `sensor.{pool}_orp` | ORP | mV | Oxidation-reduction potential reading |
| `sensor.{pool}_filtration_duration` | Recommended filtration | h | Computed recommended daily filtration hours |
| `sensor.{pool}_water_quality_score` | Water quality | % | Computed water quality score (0-100) |
| `sensor.{pool}_recommendations` | Recommendations | -- | Number of active recommendations (details in attributes) |

### Binary Sensors

| Entity | Name | Device Class | Description |
| --- | --- | --- | --- |
| `binary_sensor.{pool}_water_ok` | Water quality | Safety | ON when water chemistry has no high/critical issues |
| `binary_sensor.{pool}_action_required` | Action required | Problem | ON when any recommendation is active |

### Select

| Entity | Name | Options | Description |
| --- | --- | --- | --- |
| `select.{pool}_mode` | Pool mode | Running, Active Wintering, Passive Wintering | Controls the current operational mode |

## Screenshots

<!-- TODO: Add screenshots of the integration in action -->

*Screenshots coming soon.*

## Prerequisites

You need existing Home Assistant sensor entities providing pool measurements. At minimum:

- **Water temperature** sensor (°C)
- **pH** sensor
- **ORP** sensor (mV)

Optionally, for more accurate recommendations:

- **TAC** (Total Alkalinity) sensor (ppm)
- **CYA** (Cyanuric Acid / Stabilizer) sensor (ppm)
- **Calcium Hardness** sensor (ppm)
- **Pump switch** entity (for future pump control features)

These can come from any source -- dedicated pool probes (e.g. Flipr, iopool, Sutro),
ESPHome DIY sensors, or manual input helpers.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=noirbizarre&repository=hass-poolman&category=Integration)

Or manually add as a custom repository:

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu and select **Custom repositories**
4. Add `noirbizarre/hass-poolman` with category **Integration**
5. Install **Pool Manager** from HACS
6. Restart Home Assistant

### Manual installation

1. Copy the `custom_components/poolman` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=poolman)

Or go to **Settings > Devices & Services > Add Integration** and search for **Pool Manager**.

### Required parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| Pool name | text | My Pool | Name for your pool (used as unique identifier) |
| Volume | number (m³) | 50.0 | Pool water volume |
| Shape | select | Rectangular | Pool shape: Rectangular, Round, or Freeform |
| Pump flow rate | number (m³/h) | 10.0 | Pump flow rate |
| Temperature entity | entity | -- | Water temperature sensor |
| pH entity | entity | -- | pH sensor |
| ORP entity | entity | -- | ORP sensor |

### Optional parameters

| Parameter | Type | Description |
| --- | --- | --- |
| TAC entity | entity | Total Alkalinity sensor |
| CYA entity | entity | Cyanuric Acid / Stabilizer sensor |
| Hardness entity | entity | Calcium Hardness sensor |
| Pump entity | entity | Pump switch (reserved for future use) |

## Pool Modes

The integration supports three operational modes, selectable via the **Pool mode** entity:

- **Running**: Normal season operation. Filtration duration is computed from water temperature
  (temp / 2 rule, with a minimum ensuring at least one full water volume turnover).
  All chemistry rules are active.
- **Active Wintering**: Reduced operation during cold months. Fixed 4-hour daily filtration. Chemistry rules remain active.
- **Passive Wintering**: Pool fully shut down. No filtration. Chemistry rules are disabled.

## Contributing

Contributions are welcome. Please read the [Contribution guide](CONTRIBUTING.md) before.

Please open an [issue](https://github.com/noirbizarre/hass-poolman/issues) for bug reports or feature requests,
and submit [pull requests](https://github.com/noirbizarre/hass-poolman/pulls) for improvements.

## License

This project is licensed under the [MIT License](LICENSE).
