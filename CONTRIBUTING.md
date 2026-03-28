# Contribution guide

## CI

All pull-requests should pass CI, including linting and testing.

### Linting

We use [`prek`](https://prek.j178.dev/) to ensure every commit reaches a minimum quality level.
While it's not mandatory, it is strongly advised to install `prek` hooks in your workspace
to ensure that every commit will be automatically checked and/or formatted:

```shell
prek install
```

You can run those linters on demand for tracked files:

```shell
poe lint
```

### Tests

Tests are managed using [pytest](https://docs.pytest.org/en/stable/).
You can run them in your worksapce using:

```shell
poe test
```

## Conventional commit

We use [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/) for commit messages.

**Type** must be one of the following:

- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to our CI configuration files and scripts (e.g. GitHub workflows)
- `docs`: Documentation only changes
- `feat`: A new feature
- `fix`: A bug fix
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `style`: Changes on code formatting that do not affect the meaning of the code
- `test`: Adding missing tests or correcting existing tests
