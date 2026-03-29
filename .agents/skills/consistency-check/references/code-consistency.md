# Code Consistency Checks

Rules for verifying internal consistency within the poolman codebase.

## Check Rules

### 1. Translation Parity

Compare `custom_components/poolman/strings.json`,
`custom_components/poolman/translations/en.json`, and
`custom_components/poolman/translations/fr.json`:

**Structural parity:**

- All three files must have the exact same JSON key structure (same nesting,
  same keys at every level)
- Every key present in `strings.json` must exist in both `en.json` and `fr.json`
- No extra keys should exist in translation files that are absent from
  `strings.json`

**Content checks:**

- `en.json` values should be actual English text (not `[%key:...]` references)
- `fr.json` values should be actual French text, not English. Flag any value
  in `fr.json` that is identical to the English version in `en.json` and
  appears to be untranslated (exception: proper nouns, units, technical terms
  like "pH", "ORP", "mV" that are language-independent)
- Check for obvious typos in French translations where English spelling
  was used instead of French (e.g. `connexion` not `connection`,
  `Recommandations` not `Recommendations`)

**Completeness:**

- `strings.json` key references (`[%key:common.something]`) should resolve to
  valid Home Assistant common strings

### 2. Constant Alignment

Verify that related constants stay synchronized across files:

**`const.py` vs `domain/model.py`:**

- Shape values in `const.py` (`SHAPE_*`) must match `PoolShape` enum values
- Filtration kind values in `const.py` (`FILTRATION_KIND_*`) must match
  `FiltrationKind` enum values
- Mode values in `const.py` (`MODE_*`) must match `PoolMode` enum values
- Default values in `const.py` should be consistent with any defaults in
  model field definitions

**`const.py` vs `config_flow.py`:**

- Config keys used in the config flow must reference `const.py` constants,
  not hardcoded strings
- Default values used in form schemas should reference `const.py` defaults

**`const.py` vs platform files:**

- `PLATFORMS` list must match the actual platform modules that exist
  (`sensor.py`, `binary_sensor.py`, `select.py`)

### 3. Enum Completeness

For each enum in `domain/model.py`, verify it is fully used:

- `PoolShape`: all values appear in `strings.json` selector options and
  `config_flow.py`
- `FiltrationKind`: all values appear in `strings.json` selector options and
  `config_flow.py`
- `PoolMode`: all values appear in `select.py` options and `strings.json`
  entity state translations
- `ChemicalProduct`: all values are referenced by at least one rule in
  `domain/rules.py` or `domain/chemistry.py`
- `RecommendationType`: all values are used in at least one rule
- `RecommendationPriority`: all values are used in at least one rule
- `Severity`: all values are used somewhere in the codebase (if not, flag
  as potentially dead code)

### 4. Naming Conventions

Verify consistent naming patterns across the codebase:

**Python naming:**

- All functions and methods use `snake_case`
- All classes use `PascalCase`
- All constants use `UPPER_SNAKE_CASE`
- All enum values use `snake_case` (verify consistency within enums)

**Entity key naming:**

- Sensor keys in `SENSOR_DESCRIPTIONS` use `snake_case`
- Binary sensor keys in `BINARY_SENSOR_DESCRIPTIONS` use `snake_case`
- Translation keys match entity keys exactly

**Config key naming:**

- All `CONF_*` constants in `const.py` follow the `CONF_` prefix pattern
- Values of `CONF_*` constants use `snake_case` strings

### 5. Type Hints Completeness

Check type annotation coverage across key modules:

- `domain/model.py` - All Pydantic model fields should have type annotations
- `domain/chemistry.py` - All public functions should have parameter and
  return type annotations
- `domain/filtration.py` - All public functions should have parameter and
  return type annotations
- `domain/rules.py` - All `evaluate()` methods should have proper signatures
- `config_flow.py` - Step methods should have return type annotations
- `coordinator.py` - Public methods should have type annotations

Flag any public function or method missing parameter types or return type.

### 6. Docstring Conventions

Verify docstrings follow Google convention as specified in `AGENTS.md`:

- All public classes should have a class-level docstring
- All public functions/methods should have a docstring
- Docstrings should use Google convention format:

  ```text
  Short summary.

  Args:
      param: Description.

  Returns:
      Description.

  Raises:
      ExceptionType: Description.
  ```

- `domain/` modules are the highest priority for docstring coverage since
  they contain the core business logic

### 7. Test Coverage Alignment

Verify that test files in `tests/` mirror the source structure:

**Expected test mapping:**

| Source Module          | Expected Test File                             |
| ---------------------- | ---------------------------------------------- |
| `domain/chemistry.py`  | `tests/domain/test_chemistry.py`               |
| `domain/filtration.py` | `tests/domain/test_filtration.py`              |
| `domain/rules.py`      | `tests/domain/test_rules.py`                   |
| `domain/model.py`      | `tests/domain/test_model.py` (if logic exists) |

**Coverage checks:**

- Every `Rule` subclass should have at least one test
- Every public function in `chemistry.py` should have test coverage
- Every pool mode should be tested in `test_filtration.py`
- Test fixtures in `conftest.py` should use realistic values consistent
  with the constants in `domain/`

Flag any source module with public logic that has no corresponding test file.

### 8. Import Organization

Verify imports follow the conventions in `AGENTS.md`:

- Imports should be grouped: standard library, then third-party, then internal
- Groups should be separated by a blank line
- No wildcard imports (`from module import *`)
- Prefer explicit imports over module-level imports
- Check for unused imports (these should be caught by ruff, but verify)

### 9. Demo Alignment

Verify `demo/fake_pool_sensor/` provides fake entities matching the
integration's expectations:

- The fake sensor integration should provide sensor entities for every
  entity type the main integration expects to read from config:
    - Temperature sensor
    - pH sensor
    - ORP sensor
    - TAC sensor (optional)
    - CYA sensor (optional)
    - Hardness sensor (optional)
- Number entities in the demo should allow setting values within the
  ranges defined in `domain/chemistry.py`
- The demo `manifest.json` should be consistent with the main
  integration's requirements
