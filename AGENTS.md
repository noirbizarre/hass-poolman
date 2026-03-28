# AI Agent Rules

This file contains guidelines and conventions for AI Agents to follow when contributing code or documentation.
The general contribution guidelines are outlined in `CONTRIBUTING.md` and should be followed alongside those.

## Project Organization

- Core business logic is organized under the `custom_components/poolman/` directory with submodules based on context
- Unit tests are located in the `tests/` directory and mirror the source code structure. Prioritize test coverage.
- Onboarding/quick start documentation is provided in the `README.md`.
- Scripts are located in the `scripts/` directory for tasks and `pyproject.toml` `tool.poe.tasks` section.
- CI and release workflows are defined in the `.github/workflows/` directory.
- A demonstration with fake sensors is maintained in `demo/` and `docker-compose.yaml`

## Coding Conventions

- Use **type hints** (annotations) wherever possible to improve code quality and autocompletion suggestions.
- Function and class docstrings must be written in English and clearly describe the behavior, arguments, and return values.
- Imports should be explicit and grouped: standard library, third-party packages, then internal imports.
- Follow PEP8 formatting and use the existing linting tools in the project.
- Prefer short, well-separated classes and functions for readability and better autocompletion.
- Domain errors must be handled using specific exceptions (such as `PoolSensorNotFoundError`).
- Existing comments should not be removed unless they are outdated or incorrect.
- Add new comments to clarify the code where necessary, never the obvious
- Changes must be scoped and favor modularity and code reuse

## Security and Best Practices

- Never suggest or autocomplete secret keys, passwords, or credentials in files or environment variables.
- Where appropriate, suggest relevant unit tests in the `tests/` directory.
- Respect existing code: follow the structure, style, and conventions already present in the codebase.

## Example Completions

- Complete function arguments with type hints: `def foo(bar: str) -> int:`.
- Suggest structured docstrings using Google convention
  (see [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)).

## Tests

- Test files should be placed in the `tests/` directory and use the `test_` prefix.
- Complete tests with clear assertions and nominal cases.
- Run tests with `pytest -q <extra pytest args>` to limit output (add `-vv` with selectors if details are required).
- Run linters with `prek -q` to limit output
- New features or bug fixes should be accompanied by relevant tests to ensure coverage and prevent regressions.
- Changes to existing behavior should be reflected in updated tests.
- Existing tests should be updated in last resort.

## Documentation

- All user-facing documentation should be written in clear, concise English.
- The main `README.md` must provide an onboarding guide, project overview, and quick start instructions.
- All definitions should be documented with descriptive docstrings and, where appropriate, usage examples.
- Update documentation in parallel with code changes, including API changes, new features, and configuration updates.
- Maintain consistency in formatting and section organization across all documentation files.
- `AGENTS.md` and `CONTRIBUTING.md` should be updated with any new guidelines or changes to existing rules.
