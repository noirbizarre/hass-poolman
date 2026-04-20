"""Extensible rule engine for pool management.

Provides a base :class:`Rule` class and built-in rules for pH, sanitizer,
filtration, and more.  Each rule evaluates the current pool state and returns
zero or more :class:`~.problem.Problem` objects describing detected issues.

The :class:`RuleEngine` collects results from all registered rules and sorts
them by severity (critical first).

Design constraints
------------------
- Rules are pure functions: stateless, deterministic, no side effects.
- Rules return :class:`~.problem.Problem` objects — never raw strings or
  booleans.
- No Home Assistant dependency.

To generate actionable :class:`~.recommendation.Recommendation` objects from
the detected problems, pass the rule engine output through
:func:`~.analysis.generate_recommendations` or use
:func:`~.analysis.analyze_pool` for the full pipeline.

Example::

    engine = RuleEngine()
    problems = engine.evaluate(pool, reading, mode, manual_measures)
    for p in problems:
        print(f"[{p.severity}] {p.code}: {p.message}")
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .chemistry import (
    CYA_MAX,
    CYA_MIN,
    FREE_CHLORINE_MAX,
    FREE_CHLORINE_MIN,
    HARDNESS_MAX,
    HARDNESS_MIN,
    ORP_MAX,
    ORP_MIN_ACCEPTABLE,
    PH_MAX,
    PH_MIN,
    PH_TARGET,
    PH_TOLERANCE,
    SALT_MAX,
    SALT_MIN,
    TAC_MAX,
    TAC_MIN,
    TDS_MAX,
    TDS_MIN,
    compute_sanitizer_status,
)
from .filtration import compute_filtration_duration
from .model import (
    ManualMeasure,
    MeasureParameter,
    Pool,
    PoolMode,
    PoolReading,
    TreatmentType,
)
from .problem import MetricName, Problem, Severity


class Rule(ABC):
    """Base class for pool management rules.

    Each rule evaluates the current pool state and returns zero or more
    :class:`~.problem.Problem` objects describing detected issues.  Rules
    must be stateless and side-effect free.
    """

    @abstractmethod
    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate the rule and return detected problems.

        Args:
            pool: Pool physical characteristics.
            reading: Current sensor readings.
            mode: Current operational mode.
            manual_measures: Manual measurements recorded by the user,
                keyed by parameter.  Used by rules that compare sensor
                readings against manual measurements.

        Returns:
            List of :class:`~.problem.Problem` objects (empty if no issue
            detected).
        """


class PhRule(Rule):
    """Rule for pH level monitoring.

    Generates a :class:`~.problem.Problem` when the pH deviates from the
    target (7.2) beyond the configured tolerance.  Severity is determined by
    how far the reading is from the acceptable range:

    - Outside the min-max range (< 6.8 or > 7.8) → :attr:`~.problem.Severity.CRITICAL`
    - Delta > 3x tolerance → :attr:`~.problem.Severity.MEDIUM`
    - Delta > tolerance → :attr:`~.problem.Severity.LOW`

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` mode.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate pH level and return problems if out of range."""
        if mode == PoolMode.WINTER_PASSIVE or reading.ph is None:
            return []

        ph = reading.ph
        delta = abs(ph - PH_TARGET)

        if delta <= PH_TOLERANCE:
            return []

        direction = "too_high" if ph > PH_TARGET else "too_low"
        code = f"ph_{direction}"

        if ph < PH_MIN or ph > PH_MAX:
            severity = Severity.CRITICAL
        elif delta > PH_TOLERANCE * 3:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        message = (
            f"pH is {direction.replace('_', ' ')}: {ph:.2f}"
            f" (expected {PH_MIN}-{PH_MAX}, target {PH_TARGET})"
        )
        return [
            Problem(
                code=code,
                message=message,
                severity=severity,
                metric=MetricName.PH,
                value=ph,
                expected_range=(PH_MIN, PH_MAX),
            )
        ]


class SanitizerRule(Rule):
    """Rule for sanitizer level evaluation based on ORP.

    Evaluates ORP (Oxidation-Reduction Potential) as an indirect measure of
    sanitizer effectiveness.  Generates a :class:`~.problem.Problem` when ORP
    is outside the acceptable range.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate sanitizer via ORP and return problems if out of range."""
        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.orp is None:
            return []

        result = compute_sanitizer_status(reading, pool.treatment)
        if result is None:
            return []

        orp = reading.orp

        if orp > ORP_MAX:
            return [
                Problem(
                    code="orp_too_high",
                    message=f"ORP is too high: {orp:.0f} mV (maximum {ORP_MAX} mV)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.ORP,
                    value=orp,
                    expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
                )
            ]

        severity = Severity.CRITICAL if result.severity == Severity.CRITICAL else Severity.MEDIUM
        return [
            Problem(
                code="orp_too_low",
                message=(
                    f"ORP is too low: {orp:.0f} mV (minimum acceptable {ORP_MIN_ACCEPTABLE} mV)"
                ),
                severity=severity,
                metric=MetricName.ORP,
                value=orp,
                expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
            )
        ]


class FreeChlorineRule(Rule):
    """Rule for free chlorine level evaluation.

    Supplements the ORP-based :class:`SanitizerRule` with a direct chlorine
    reading.  Low free chlorine (< 1 ppm) is critical; high free chlorine
    (> 3 ppm) is a low-severity alert.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate free chlorine level and return problems if out of range."""
        if (
            mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or reading.free_chlorine is None
        ):
            return []

        fc = reading.free_chlorine

        if fc < FREE_CHLORINE_MIN:
            return [
                Problem(
                    code="chlorine_too_low",
                    message=(
                        f"Free chlorine is too low: {fc:.1f} ppm (minimum {FREE_CHLORINE_MIN} ppm)"
                    ),
                    severity=Severity.CRITICAL,
                    metric=MetricName.CHLORINE,
                    value=fc,
                    expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                )
            ]

        if fc > FREE_CHLORINE_MAX:
            return [
                Problem(
                    code="chlorine_too_high",
                    message=(
                        f"Free chlorine is too high: {fc:.1f} ppm (maximum {FREE_CHLORINE_MAX} ppm)"
                    ),
                    severity=Severity.LOW,
                    metric=MetricName.CHLORINE,
                    value=fc,
                    expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                )
            ]

        return []


class FiltrationRule(Rule):
    """Rule for filtration duration monitoring.

    Generates a :class:`~.problem.Problem` when a filtration duration can be
    computed, serving as a signal for the analysis layer to produce a
    filtration recommendation.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` mode.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate filtration needs and return a problem when action is due."""
        if mode == PoolMode.WINTER_PASSIVE:
            return []

        hours = compute_filtration_duration(pool, reading, mode)
        if hours is None:
            return []

        severity = Severity.MEDIUM if hours >= 12 else Severity.LOW
        return [
            Problem(
                code="filtration_required",
                message=f"Run filtration for {hours:.1f} hours today",
                severity=severity,
                metric=None,
                value=hours,
                expected_range=None,
            )
        ]


class TacRule(Rule):
    """Rule for total alkalinity (TAC) adjustment.

    Generates a :class:`~.problem.Problem` when TAC is outside the acceptable
    range (80-150 ppm).

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate TAC level and return problems if out of range."""
        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.tac is None:
            return []

        tac = reading.tac

        if tac < TAC_MIN:
            return [
                Problem(
                    code="alkalinity_too_low",
                    message=f"Total alkalinity is too low: {tac:.0f} ppm (minimum {TAC_MIN} ppm)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.ALKALINITY,
                    value=tac,
                    expected_range=(TAC_MIN, TAC_MAX),
                )
            ]

        if tac > TAC_MAX:
            return [
                Problem(
                    code="alkalinity_too_high",
                    message=f"Total alkalinity is too high: {tac:.0f} ppm (maximum {TAC_MAX} ppm)",
                    severity=Severity.LOW,
                    metric=MetricName.ALKALINITY,
                    value=tac,
                    expected_range=(TAC_MIN, TAC_MAX),
                )
            ]

        return []


class AlgaeRiskRule(Rule):
    """Rule for algae risk detection based on temperature and ORP.

    Generates a critical :class:`~.problem.Problem` when the water temperature
    exceeds 28 °C and ORP is below the acceptable minimum simultaneously,
    indicating high algae growth risk.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate algae risk from warm water and low ORP."""
        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE):
            return []

        if reading.temp_c is None or reading.orp is None:
            return []

        if reading.temp_c > 28 and reading.orp < ORP_MIN_ACCEPTABLE:
            return [
                Problem(
                    code="algae_risk",
                    message=(
                        f"High algae risk: water temperature {reading.temp_c:.1f} °C"
                        f" with ORP {reading.orp:.0f} mV"
                    ),
                    severity=Severity.CRITICAL,
                    metric=MetricName.ORP,
                    value=reading.orp,
                    expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
                )
            ]

        return []


class CyaRule(Rule):
    """Rule for cyanuric acid (CYA / stabilizer) level monitoring.

    CYA below minimum (20 ppm) requires adding stabilizer.
    CYA above maximum (75 ppm) has no chemical fix; recommends partial drain.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate CYA level and return problems if out of range."""
        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.cya is None:
            return []

        cya = reading.cya

        if cya < CYA_MIN:
            return [
                Problem(
                    code="cya_too_low",
                    message=f"CYA is too low: {cya:.0f} ppm (minimum {CYA_MIN} ppm)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.CYA,
                    value=cya,
                    expected_range=(CYA_MIN, CYA_MAX),
                )
            ]

        if cya > CYA_MAX:
            return [
                Problem(
                    code="cya_too_high",
                    message=f"CYA is too high: {cya:.0f} ppm (maximum {CYA_MAX} ppm)",
                    severity=Severity.LOW,
                    metric=MetricName.CYA,
                    value=cya,
                    expected_range=(CYA_MIN, CYA_MAX),
                )
            ]

        return []


class HardnessRule(Rule):
    """Rule for calcium hardness level monitoring.

    Hardness below minimum (150 ppm) requires adding calcium hardness
    increaser.  Hardness above maximum (400 ppm) has no chemical fix;
    recommends partial drain.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate calcium hardness and return problems if out of range."""
        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.hardness is None:
            return []

        hardness = reading.hardness

        if hardness < HARDNESS_MIN:
            return [
                Problem(
                    code="hardness_too_low",
                    message=(
                        f"Calcium hardness is too low: {hardness:.0f} ppm"
                        f" (minimum {HARDNESS_MIN} ppm)"
                    ),
                    severity=Severity.MEDIUM,
                    metric=MetricName.HARDNESS,
                    value=hardness,
                    expected_range=(HARDNESS_MIN, HARDNESS_MAX),
                )
            ]

        if hardness > HARDNESS_MAX:
            return [
                Problem(
                    code="hardness_too_high",
                    message=(
                        f"Calcium hardness is too high: {hardness:.0f} ppm"
                        f" (maximum {HARDNESS_MAX} ppm)"
                    ),
                    severity=Severity.LOW,
                    metric=MetricName.HARDNESS,
                    value=hardness,
                    expected_range=(HARDNESS_MIN, HARDNESS_MAX),
                )
            ]

        return []


class SaltRule(Rule):
    """Rule for salt level monitoring in salt electrolysis pools.

    Only evaluates when the pool treatment is
    :attr:`~.model.TreatmentType.SALT_ELECTROLYSIS`.
    Salt below minimum (2700 ppm) requires adding salt.
    Salt above maximum (3400 ppm) recommends partial drain.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` and
    :attr:`~.model.PoolMode.WINTER_ACTIVE` modes.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate salt level and return problems if out of range."""
        if pool.treatment != TreatmentType.SALT_ELECTROLYSIS:
            return []

        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.salt is None:
            return []

        salt = reading.salt

        if salt < SALT_MIN:
            return [
                Problem(
                    code="salt_too_low",
                    message=f"Salt level is too low: {salt:.0f} ppm (minimum {SALT_MIN} ppm)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.SALT,
                    value=salt,
                    expected_range=(SALT_MIN, SALT_MAX),
                )
            ]

        if salt > SALT_MAX:
            return [
                Problem(
                    code="salt_too_high",
                    message=f"Salt level is too high: {salt:.0f} ppm (maximum {SALT_MAX} ppm)",
                    severity=Severity.LOW,
                    metric=MetricName.SALT,
                    value=salt,
                    expected_range=(SALT_MIN, SALT_MAX),
                )
            ]

        return []


class TdsRule(Rule):
    """Rule for Total Dissolved Solids (TDS) monitoring.

    TDS is derived from EC and indicates the concentration of dissolved
    minerals in the water.  High TDS reduces sanitizer effectiveness and
    can cause cloudy water.

    Skipped for salt electrolysis pools because dissolved salt naturally
    raises TDS well above the freshwater thresholds.  Also skipped in
    winter modes.

    TDS above maximum recommends a partial water drain (no chemical can
    lower dissolved solids).  TDS below minimum suggests sensor calibration.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Evaluate TDS level and return problems when out of range."""
        # Salt electrolysis pools naturally have high TDS from dissolved salt
        if pool.treatment == TreatmentType.SALT_ELECTROLYSIS:
            return []

        if mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE) or reading.tds is None:
            return []

        tds = reading.tds

        if tds > TDS_MAX:
            return [
                Problem(
                    code="tds_too_high",
                    message=f"TDS is too high: {tds:.0f} ppm (maximum {TDS_MAX} ppm)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.TDS,
                    value=tds,
                    expected_range=(TDS_MIN, TDS_MAX),
                )
            ]

        if tds < TDS_MIN:
            return [
                Problem(
                    code="tds_too_low",
                    message=f"TDS is unusually low: {tds:.0f} ppm (minimum {TDS_MIN} ppm)",
                    severity=Severity.LOW,
                    metric=MetricName.TDS,
                    value=tds,
                    expected_range=(TDS_MIN, TDS_MAX),
                )
            ]

        return []


# Deviation thresholds per parameter for calibration checks.
# When the absolute difference between a sensor reading and the last manual
# measurement exceeds these values, a calibration problem is generated.
_CALIBRATION_THRESHOLDS: dict[MeasureParameter, float] = {
    MeasureParameter.PH: 0.3,
    MeasureParameter.ORP: 50.0,
    MeasureParameter.FREE_CHLORINE: 0.5,
    MeasureParameter.EC: 100.0,
    MeasureParameter.TDS: 50.0,
    MeasureParameter.SALT: 100.0,
    MeasureParameter.TAC: 20.0,
    MeasureParameter.CYA: 10.0,
    MeasureParameter.HARDNESS: 50.0,
    MeasureParameter.TEMPERATURE: 2.0,
}

# Mapping from MeasureParameter to the corresponding PoolReading field name
_MEASURE_TO_READING_FIELD: dict[MeasureParameter, str] = {
    MeasureParameter.PH: "ph",
    MeasureParameter.ORP: "orp",
    MeasureParameter.FREE_CHLORINE: "free_chlorine",
    MeasureParameter.EC: "ec",
    MeasureParameter.TDS: "tds",
    MeasureParameter.SALT: "salt",
    MeasureParameter.TAC: "tac",
    MeasureParameter.CYA: "cya",
    MeasureParameter.HARDNESS: "hardness",
    MeasureParameter.TEMPERATURE: "temp_c",
}

# Human-readable labels for measure parameters
_MEASURE_LABELS: dict[MeasureParameter, str] = {
    MeasureParameter.PH: "pH",
    MeasureParameter.ORP: "ORP",
    MeasureParameter.FREE_CHLORINE: "free chlorine",
    MeasureParameter.EC: "EC",
    MeasureParameter.TDS: "TDS",
    MeasureParameter.SALT: "salt",
    MeasureParameter.TAC: "TAC",
    MeasureParameter.CYA: "CYA",
    MeasureParameter.HARDNESS: "hardness",
    MeasureParameter.TEMPERATURE: "temperature",
}


class CalibrationRule(Rule):
    """Rule that detects deviation between sensor readings and manual measurements.

    When both a sensor value and a manual measurement exist for the same
    parameter, compares them.  If the deviation exceeds a per-parameter
    threshold, generates a :class:`~.problem.Problem` with
    :attr:`~.problem.Severity.LOW` suggesting sensor recalibration.

    Disabled in :attr:`~.model.PoolMode.WINTER_PASSIVE` mode.
    Requires at least one manual measurement to be recorded.
    """

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Compare sensor readings against manual measures and flag deviations."""
        if mode == PoolMode.WINTER_PASSIVE or not manual_measures:
            return []

        problems: list[Problem] = []
        for param, measure in manual_measures.items():
            threshold = _CALIBRATION_THRESHOLDS.get(param)
            if threshold is None:
                continue

            field_name = _MEASURE_TO_READING_FIELD.get(param)
            if field_name is None:
                continue

            sensor_value = getattr(reading, field_name, None)
            if sensor_value is None:
                continue

            deviation = abs(sensor_value - measure.value)
            if deviation > threshold:
                label = _MEASURE_LABELS.get(param, param.value)
                problems.append(
                    Problem(
                        code=f"calibration_{param.value}",
                        message=(
                            f"{label} sensor reading ({sensor_value:.1f}) deviates from"
                            f" manual measure ({measure.value:.1f}) by {deviation:.1f}"
                            f" (threshold {threshold})."
                            " Consider sensor recalibration or a new manual measurement."
                        ),
                        severity=Severity.LOW,
                        metric=None,
                        value=sensor_value,
                        expected_range=None,
                    )
                )

        return problems


class RuleEngine:
    """Engine that evaluates all registered rules against pool state.

    Rules are evaluated in registration order.  All detected
    :class:`~.problem.Problem` objects are collected and returned sorted by
    severity (critical first).

    Example::

        engine = RuleEngine()
        problems = engine.evaluate(pool, reading, mode)
        for problem in problems:
            print(f"[{problem.severity}] {problem.code}: {problem.message}")
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        """Initialize the rule engine with optional rules.

        Args:
            rules: List of rules to register.  If ``None``, uses the default
                set of built-in rules.
        """
        self.rules = rules if rules is not None else self._default_rules()

    @staticmethod
    def _default_rules() -> list[Rule]:
        """Return the default set of built-in rules."""
        return [
            PhRule(),
            SanitizerRule(),
            FreeChlorineRule(),
            FiltrationRule(),
            TacRule(),
            AlgaeRiskRule(),
            CyaRule(),
            HardnessRule(),
            SaltRule(),
            TdsRule(),
            CalibrationRule(),
        ]

    def evaluate(
        self,
        pool: Pool,
        reading: PoolReading,
        mode: PoolMode,
        manual_measures: dict[MeasureParameter, ManualMeasure] | None = None,
    ) -> list[Problem]:
        """Run all rules and collect detected problems.

        Args:
            pool: Pool physical characteristics.
            reading: Current sensor readings.
            mode: Current operational mode.
            manual_measures: Manual measurements recorded by the user.

        Returns:
            All problems from all rules, sorted by severity (critical first).
        """
        problems: list[Problem] = []
        for rule in self.rules:
            problems.extend(rule.evaluate(pool, reading, mode, manual_measures=manual_measures))

        # Sort by severity (critical first)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.MEDIUM: 1,
            Severity.LOW: 2,
        }
        problems.sort(key=lambda p: severity_order.get(p.severity, 99))

        return problems
