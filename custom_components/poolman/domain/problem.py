"""Canonical problem types for pool water-quality diagnostics.

This module is the single source of truth for:

- :class:`Severity` -- how serious a problem is.
- :class:`MetricName` -- canonical names for the pool chemistry metrics.
- :class:`ChemistryStatus` -- good / warning / bad status for a single
  parameter.
- :class:`ParameterReport` -- a self-describing status report for one metric.
- :class:`Problem` -- a normalized representation of a single water-quality
  issue.
- :func:`detect_problems` -- derives a list of :class:`Problem` objects from a
  :class:`~.model.PoolState` snapshot.

These types are imported by :mod:`.model`, :mod:`.recommendation`, and
:mod:`.analysis`; they must never depend on those modules (no circular
imports).

No Home Assistant dependency is present in this module.

Example::

    from custom_components.poolman.domain.problem import detect_problems

    problems = detect_problems(pool_state)
    for p in problems:
        print(f"[{p.severity}] {p.code}: {p.message}")
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Severity(StrEnum):
    """Severity levels for a detected water-quality problem.

    Ordered from least to most urgent:

    - :attr:`LOW` -- parameter is drifting toward a boundary but still within
      the acceptable range.  Monitor; no immediate action required.
    - :attr:`MEDIUM` -- parameter is slightly outside the acceptable range.
      Action is recommended soon.
    - :attr:`CRITICAL` -- parameter is far outside the acceptable range.
      Immediate action is required.

    All values serialize as plain strings (``"low"``, ``"medium"``,
    ``"critical"``) because :class:`Severity` inherits from
    :class:`~enum.StrEnum`.
    """

    LOW = "low"
    MEDIUM = "medium"
    CRITICAL = "critical"


class MetricName(StrEnum):
    """Canonical names for pool chemistry metrics.

    Used to identify the parameter a :class:`Problem` or
    :class:`~.recommendation.Recommendation` relates to in a strongly-typed,
    serialisation-friendly way.

    All values serialize as plain strings (``"ph"``, ``"orp"``, …) because
    :class:`MetricName` inherits from :class:`~enum.StrEnum`.

    Attributes:
        PH: Potential of Hydrogen -- controls scale, equipment corrosion, and
            sanitiser effectiveness.
        ORP: Oxidation-Reduction Potential -- indirect measure of sanitiser
            effectiveness (mV).
        CHLORINE: Free chlorine concentration (ppm) -- direct sanitiser
            measurement.
        TEMPERATURE: Water temperature (°C).
        CYA: Cyanuric acid / stabiliser -- protects chlorine from UV
            degradation (ppm).
        ALKALINITY: Total alkalinity (TAC) -- pH buffer capacity (ppm).
        HARDNESS: Calcium hardness -- prevents corrosion and scaling (ppm).
        TDS: Total dissolved solids -- overall mineral load, derived from EC
            (ppm).
        SALT: Salt concentration -- relevant for salt-electrolysis pools (ppm).
        EC: Electrical conductivity (µS/cm) -- used to derive TDS.
    """

    PH = "ph"
    ORP = "orp"
    CHLORINE = "chlorine"
    TEMPERATURE = "temperature"
    CYA = "cya"
    ALKALINITY = "alkalinity"
    HARDNESS = "hardness"
    TDS = "tds"
    SALT = "salt"
    EC = "ec"


class ChemistryStatus(StrEnum):
    """Status levels for individual chemistry parameters.

    Assigned by comparing a parameter's quality score against thresholds:

    - :attr:`GOOD` -- score >= 50, parameter is close to target.
    - :attr:`WARNING` -- score < 50 but value is within the min-max range;
      parameter is drifting toward a boundary.
    - :attr:`BAD` -- value is outside the acceptable min-max range.
    """

    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"


# ---------------------------------------------------------------------------
# Parameter report (lives here to avoid circular imports with model.py)
# ---------------------------------------------------------------------------


class ParameterReport(BaseModel, frozen=True):
    """Status report for a single chemistry parameter.

    Bundles the metric identity with the evaluated status, the reading value,
    target range, and individual quality score for rich dashboard display.
    The :attr:`metric` field makes each report self-describing so callers
    never need an external mapping from field name to metric name.

    Attributes:
        metric: Canonical name for the affected pool chemistry parameter.
        status: Evaluated quality status for this parameter.
        value: Actual sensor reading for this parameter.
        target: Ideal target value used for scoring.
        minimum: Lower bound of the acceptable range.
        maximum: Upper bound of the acceptable range.
        score: Per-parameter quality score (0 = at/beyond boundary,
            100 = at target).
    """

    metric: MetricName
    status: ChemistryStatus
    value: float
    target: float
    minimum: float
    maximum: float
    score: int = Field(ge=0, le=100, description="Quality score from 0 to 100")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Human-readable labels used in problem messages.
_METRIC_LABELS: dict[MetricName, str] = {
    MetricName.PH: "pH",
    MetricName.ORP: "ORP",
    MetricName.CHLORINE: "free chlorine",
    MetricName.TDS: "TDS",
    MetricName.SALT: "salt",
    MetricName.ALKALINITY: "TAC",
    MetricName.CYA: "CYA",
    MetricName.HARDNESS: "hardness",
    MetricName.TEMPERATURE: "temperature",
}

# Sort key for ordering problems critical-first.
_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
}


def _direction(value: float, minimum: float, maximum: float) -> str:
    """Return ``'too_high'`` or ``'too_low'`` based on which boundary is crossed.

    When the value is within range this helper should not be called; it falls
    back to ``'out_of_range'`` for safety.

    Args:
        value: The actual measured value.
        minimum: Lower bound of the acceptable range.
        maximum: Upper bound of the acceptable range.

    Returns:
        Direction string: ``'too_high'``, ``'too_low'``, or ``'out_of_range'``.
    """
    if value > maximum:
        return "too_high"
    if value < minimum:
        return "too_low"
    return "out_of_range"


def _severity_for(report: ParameterReport) -> Severity:
    """Map a :class:`ParameterReport` status and score to a :class:`Severity`.

    Mapping rules:

    * ``warning`` → :attr:`Severity.LOW` (value is near but still within the
      acceptable range boundaries).
    * ``bad`` with ``score > 0`` → :attr:`Severity.MEDIUM` (slightly outside
      the acceptable range).
    * ``bad`` with ``score == 0`` → :attr:`Severity.CRITICAL` (far outside the
      acceptable range).

    Args:
        report: The parameter report to classify.

    Returns:
        The corresponding :class:`Severity` level.
    """
    if report.status == ChemistryStatus.WARNING:
        return Severity.LOW
    # status == BAD
    if report.score > 0:
        return Severity.MEDIUM
    return Severity.CRITICAL


def _make_problem(report: ParameterReport) -> Problem:
    """Build a :class:`Problem` from a self-describing :class:`ParameterReport`.

    The metric name, value, and expected range are read directly from the
    report — no external field-to-metric mapping is required.

    Args:
        report: The evaluated :class:`ParameterReport` for an abnormal
            parameter.

    Returns:
        A fully populated :class:`Problem` instance.
    """
    metric = report.metric
    severity = _severity_for(report)
    label = _METRIC_LABELS.get(metric, str(metric))
    dir_str = _direction(report.value, report.minimum, report.maximum)

    code = f"{metric}_{dir_str}"
    message = (
        f"{label} is {dir_str.replace('_', ' ')}: "
        f"{report.value} (expected {report.minimum}-{report.maximum})"
    )

    return Problem(
        code=code,
        message=message,
        severity=severity,
        metric=metric,
        value=report.value,
        expected_range=(report.minimum, report.maximum),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Problem:
    """A normalized representation of a single water-quality issue.

    A :class:`Problem` is generated for every chemistry parameter that deviates
    from its acceptable range.  It carries enough information for dashboards,
    logs, and downstream services to understand the nature and urgency of the
    issue without containing any treatment advice.

    All fields except :attr:`code`, :attr:`message`, and :attr:`severity` are
    optional to support partial or missing sensor data gracefully.

    Attributes:
        code: Machine-readable identifier, e.g. ``"ph_too_high"`` or
            ``"orp_too_low"``.  Follows the pattern
            ``"{metric}_{direction}"`` where direction is one of
            ``"too_high"``, ``"too_low"``, or ``"out_of_range"``.
        message: Human-readable description of the problem, including the
            measured value and expected range.
        severity: How serious the deviation is
            (:attr:`Severity.LOW`, :attr:`Severity.MEDIUM`, or
            :attr:`Severity.CRITICAL`).
        metric: The canonical :class:`MetricName` for the affected parameter,
            or ``None`` when the parameter has no known mapping.
        value: The actual measured value that triggered the problem, or
            ``None`` when the value is unavailable.
        expected_range: ``(minimum, maximum)`` tuple representing the
            acceptable range for this parameter, or ``None`` when the range
            is unknown.
    """

    code: str
    message: str
    severity: Severity
    metric: MetricName | None
    value: float | None
    expected_range: tuple[float, float] | None


def detect_problems(pool_state: object) -> list[Problem]:
    """Detect all chemistry problems present in a pool state snapshot.

    Iterates over every parameter in the pool state's ``chemistry_report``
    and returns a :class:`Problem` for each one whose status is not
    :attr:`ChemistryStatus.GOOD`.

    The function is resilient to missing data: ``None`` readings are skipped,
    and any unexpected error while evaluating a single parameter is logged and
    skipped rather than propagated.

    The result is ordered from most to least severe
    (:attr:`Severity.CRITICAL` first, then :attr:`Severity.MEDIUM`, then
    :attr:`Severity.LOW`).

    Args:
        pool_state: The current pool state snapshot produced by the
            coordinator.  Expected to have a ``chemistry_report`` attribute
            of type :class:`~.model.ChemistryReport`.

    Returns:
        A list of :class:`Problem` instances, empty when all parameters are
        within acceptable ranges or no readings are available.

    Example::

        state = coordinator.data
        problems = detect_problems(state)
        for problem in problems:
            print(f"[{problem.severity}] {problem.code}: {problem.message}")
    """
    report = getattr(pool_state, "chemistry_report", None)
    if report is None:
        return []

    problems: list[Problem] = []
    for field in report.model_fields:
        param_report: ParameterReport | None = getattr(report, field, None)
        if param_report is None:
            continue
        if param_report.status == ChemistryStatus.GOOD:
            continue
        try:
            problems.append(_make_problem(param_report))
        except Exception:
            _LOGGER.exception("Unexpected error while building Problem for field %r", field)

    problems.sort(key=lambda p: _SEVERITY_ORDER[p.severity])
    return problems
