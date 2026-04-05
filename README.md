<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD041 -->
<p align="center">
  <img src="docs/images/logo.svg" alt="Pool Manager logo" />
</p>
<p align="center">
  A virtual pool management advisor for Home Assistant.
</p>
<p align="center">
  <a href="https://github.com/noirbizarre/hass-poolman/actions/workflows/ci.yaml">
    <img src="https://github.com/noirbizarre/hass-poolman/actions/workflows/ci.yaml/badge.svg" alt="CI">
  </a>
  <a href="https://codecov.io/gh/noirbizarre/hass-poolman">
    <img src="https://codecov.io/gh/noirbizarre/hass-poolman/graph/badge.svg" alt="Codecov">
  </a>
  <img src="https://img.shields.io/github/v/release/noirbizarre/hass-poolman" alt="Release">
  <img src="https://img.shields.io/github/license/noirbizarre/hass-poolman" alt="License">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS">
  </a>
</p>

---

# Pool Manager

**Pool Manager** is a Home Assistant custom integration that aggregates
readings from your existing sensor entities (pH, ORP, temperature, etc.)
and computes actionable pool management insights -- all locally, with no
cloud service or specific hardware required.

## Features

- **Computed analytics**: recommended daily filtration duration and a 0-100% water quality score
- **Rule engine**: actionable recommendations with chemical product names and dosage in grams
- **5 operational modes**: Active, Activating, Hibernating, Active Wintering, Passive Wintering
- **Hardware agnostic**: works with any pool sensor source (Flipr, iopool, Sutro, ESPHome, manual input)
- **Multi-language**: English and French translations included

## Installation

<!-- markdownlint-disable MD013 -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=noirbizarre&repository=hass-poolman&category=Integration)
<!-- markdownlint-enable MD013 -->

Or manually: copy `custom_components/poolman` into your
`config/custom_components/` directory and restart Home Assistant.

## Documentation

Full documentation is available at **[noirbizarre.github.io/hass-poolman](https://noirbizarre.github.io/hass-poolman/)**.

## Contributing

Contributions are welcome. Please read the [Contribution guide](CONTRIBUTING.md) before submitting changes.

- [Report a bug](https://github.com/noirbizarre/hass-poolman/issues)
- [Request a feature](https://github.com/noirbizarre/hass-poolman/issues)
- [Submit a pull request](https://github.com/noirbizarre/hass-poolman/pulls)

## License

This project is licensed under the [MIT License](LICENSE).
