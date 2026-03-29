# Documentation-Code Consistency Checks

Rules for verifying that documentation accurately reflects the current codebase
in the poolman project.

## Check Rules

### 1. Entity Documentation vs Platform Code

Compare `docs/entities.md` against the actual platform implementations:

**Sensors** — compare against `custom_components/poolman/sensor.py`
(`SENSOR_DESCRIPTIONS`):

| Doc Claim         | Code to Verify                                 |
| ----------------- | ---------------------------------------------- |
| Entity keys/names | `key` field in each `PoolmanSensorDescription` |
| Device classes    | `device_class` field                           |
| Units of measure  | `native_unit_of_measurement` field             |
| Icons             | `icon` field                                   |
| State source      | `value_fn` lambda or `state_fn`                |
| Extra attributes  | `extra_state_attributes` in entity code        |

Expected sensors: `temperature`, `ph`, `orp`, `filtration_duration`,
`water_quality_score`, `recommendations`.

**Binary sensors** — compare against `custom_components/poolman/binary_sensor.py`
(`BINARY_SENSOR_DESCRIPTIONS`):

| Doc Claim         | Code to Verify                         |
| ----------------- | -------------------------------------- |
| Entity keys/names | `key` field                            |
| Device classes    | `device_class` field (safety, problem) |
| ON/OFF semantics  | `is_on` property or `value_fn`         |

Expected binary sensors: `water_ok`, `action_required`.

**Select entities** — compare against `custom_components/poolman/select.py`:

| Doc Claim         | Code to Verify                                   |
| ----------------- | ------------------------------------------------ |
| Entity key        | `key` field in `SELECT_DESCRIPTION`              |
| Available options | `options` field (should match `PoolMode` values) |
| Behavior          | `async_select_option` implementation             |

Expected selects: `mode` with options `running`, `winter_active`,
`winter_passive`.

Flag any entity documented but not in code, or in code but not documented.

### 2. Pool Modes Documentation vs Code

Compare `docs/pool-modes.md` against `custom_components/poolman/domain/model.py`
(`PoolMode` enum) and `custom_components/poolman/domain/filtration.py`:

- Every `PoolMode` enum value must be documented
- Filtration behavior per mode must match:
    - Running: temp/2 rule, clamped to `MIN_FILTRATION_HOURS`-`MAX_FILTRATION_HOURS`,
    adjusted for pump turnover
    - Active wintering: fixed `WINTER_ACTIVE_HOURS` (4h)
    - Passive wintering: fixed `WINTER_PASSIVE_HOURS` (0h)
- Minimum/maximum filtration hours in docs must match constants in `filtration.py`
- Rule activation table in docs must match which rules check
  `mode == PoolMode.WINTER_PASSIVE` to disable themselves in `rules.py`

### 3. Water Chemistry Documentation vs Code

Compare `docs/water-chemistry.md` against
`custom_components/poolman/domain/chemistry.py`:

**Parameter ranges** — verify these exact values match between docs and code:

| Parameter | Code Constants                                    | Doc Section      |
| --------- | ------------------------------------------------- | ---------------- |
| pH        | `PH_MIN`, `PH_TARGET`, `PH_MAX`                   | Parameter ranges |
| ORP       | `ORP_MIN_CRITICAL`, `ORP_TARGET`, `ORP_MAX`       | Parameter ranges |
| TAC       | `TAC_MIN`, `TAC_TARGET`, `TAC_MAX`                | Parameter ranges |
| CYA       | `CYA_MIN`, `CYA_TARGET`, `CYA_MAX`                | Parameter ranges |
| Hardness  | `HARDNESS_MIN`, `HARDNESS_TARGET`, `HARDNESS_MAX` | Parameter ranges |

**Dosage formulas** — verify documented formulas match code implementations:

- pH dosage formula in docs must match `compute_ph_adjustment()` logic
  (expected: `|pH - PH_TARGET| / PH_DOSAGE_STEP * PH_DOSAGE_PER_10M3 * volume/10`)
- TAC dosage formula in docs must match `compute_tac_adjustment()` logic

**Water quality score** — verify:

- Scoring method described (0-100% per parameter, averaged) matches
  `compute_water_quality_score()` and `_score_range()`
- Which parameters contribute to the score matches code

**Chemical products** — verify every `ChemicalProduct` enum value in
`domain/model.py` is documented with its purpose.

### 4. Rules Documentation vs Code

Compare `docs/rules-and-recommendations.md` against
`custom_components/poolman/domain/rules.py`:

**Rule inventory** — every `Rule` subclass must be documented and vice versa:

Expected rules: `PhRule`, `ChlorineRule`, `FiltrationRule`, `TacRule`,
`AlgaeRiskRule`.

**Per-rule checks:**

| Rule           | Doc Claims to Verify Against Code                          |
| -------------- | ---------------------------------------------------------- |
| PhRule         | Threshold values, priority levels, disable in passive mode |
| ChlorineRule   | ORP thresholds, priority levels, disable in passive mode   |
| FiltrationRule | Duration thresholds, priority levels, wintering behavior   |
| TacRule        | TAC thresholds, priority levels, disable in passive mode   |
| AlgaeRiskRule  | Temperature + ORP conditions, priority, disable condition  |

**Priority system** — verify:

- `RecommendationPriority` enum values match the documented priority levels
- The documented effect of each priority on `water_ok` and `action_required`
  matches the `PoolState` property implementations in `domain/model.py`
- `water_ok` should be False only when HIGH or CRITICAL recommendations exist
- `action_required` should be True when ANY recommendations exist

**Recommendation types** — verify `RecommendationType` enum values match
documentation.

### 5. Getting Started Documentation vs Config Flow

Compare `docs/getting-started.md` against
`custom_components/poolman/config_flow.py` and `custom_components/poolman/const.py`:

- Config steps described in docs must match `config_flow.py` step methods
- Required vs optional sensors in docs must match which config fields have
  defaults vs are mandatory
- Default values mentioned in docs must match constants in `const.py`
  (e.g. `DEFAULT_VOLUME_M3`, `DEFAULT_PUMP_FLOW_M3H`, `DEFAULT_FILTRATION_KIND`)
- Value ranges in docs (min/max for volume, pump flow) must match
  `vol_schema` / `number` validators in `config_flow.py`
- Update interval mentioned in docs must match `DEFAULT_UPDATE_INTERVAL_MINUTES`

### 6. README vs Manifest

Compare `README.md` against `custom_components/poolman/manifest.json`:

- Integration name consistency
- Version references (if any in README)
- Documentation URL
- Requirements mentioned
- HA version compatibility claims
