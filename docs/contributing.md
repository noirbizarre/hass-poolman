---
icon: lucide/heart-handshake
---

# Contributing

Contributions to Pool Manager are welcome.

## How to Contribute

Please read the [Contribution guide][contributing] for details on linting,
testing, and commit conventions.

[contributing]: https://github.com/noirbizarre/hass-poolman/blob/main/CONTRIBUTING.md

- **Bug reports**: Open an [issue][issues] with steps to reproduce
- **Feature requests**: Open an [issue][issues] describing the use case
- **Pull requests**: Submit a [pull request][prs] with your changes

[issues]: https://github.com/noirbizarre/hass-poolman/issues
[prs]: https://github.com/noirbizarre/hass-poolman/pulls

## Development Quick Start

Pool Manager uses [uv](https://docs.astral.sh/uv/) for dependency management
and [poethepoet](https://poethepoet.natn.io/) as task runner.

```shell
# Install dependencies
uv sync --frozen --all-groups

# Run linters
poe lint

# Run tests
poe test

# Build documentation locally
poe doc
```

## License

This project is licensed under the [MIT License](https://github.com/noirbizarre/hass-poolman/blob/main/LICENSE).
