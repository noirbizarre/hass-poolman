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

The Lovelace cards have their own unit tests (Vitest) under `frontend/`:

```shell
cd frontend && npm test
```

### End-to-end tests

Browser-based end-to-end tests live in `e2e/` and use
[Playwright](https://playwright.dev/). They drive the docker-compose demo
Home Assistant instance and verify the custom Lovelace cards.

First-time setup:

```shell
cd e2e
npm install
npx playwright install chromium
```

Run the suite (Playwright starts the demo stack automatically via
`docker compose up -d --wait`):

```shell
npm test
```

For faster iteration, start the stack yourself and reuse it:

```shell
docker compose up -d          # from the repository root, wait for "All done!"
cd e2e && npm test            # reuses the running instance
npm run test:ui               # interactive runner
npm run report                # open the HTML report
```

Reset the instance between runs with `docker compose down -v`.

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
