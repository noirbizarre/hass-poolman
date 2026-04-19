"""Problem detection for pool chemistry.

This module provides a normalized :class:`Problem` representation for abnormal
chemistry metrics and the :func:`detect_problems` function that derives a list
of problems from a :class:`~.model.PoolState` snapshot.

No treatment logic is included here — problems only describe *what* is wrong,
not *how* to fix it.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass

from .model import ChemistryStatus, MetricName, ParameterReport, PoolState, Severity

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping from ChemistryReport field names to MetricName enum values
# ---------------------------------------------------------------------------

_FIELD_TO_METRIC: dict[str, MetricName] = {
    "ph": MetricName.PH,
    "orp": MetricName.ORP,
    "free_chlorine": MetricName.CHLORINE,
    "tds": MetricName.TDS,
    "salt": MetricName.SALT,
    "tac": MetricName.ALKALINITY,
    "cya": MetricName.CYA,
    "hardness": MetricName.HARDNESS,
}

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

_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
      acceptable range boundaries)
    * ``bad`` with ``score > 0`` → :attr:`Severity.MEDIUM` (slightly outside
      the acceptable range)
    * ``bad`` with ``score == 0`` → :attr:`Severity.CRITICAL` (far outside the
      acceptable range)

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


def _make_problem(field: str, report: ParameterReport) -> Problem:
    """Build a :class:`Problem` from a ChemistryReport field name and its report.

    The ``metric`` field is populated from the :data:`_FIELD_TO_METRIC` mapping
    when available, and ``None`` otherwise. Likewise, ``value`` and
    ``expected_range`` are taken from the report when present.

    Args:
        field: The ``ChemistryReport`` attribute name (e.g. ``"ph"``).
        report: The evaluated :class:`ParameterReport` for that parameter.

    Returns:
        A fully populated :class:`Problem` instance.
    """
    metric = _FIELD_TO_METRIC.get(field)
    severity = _severity_for(report)

    value: float | None = report.value
    expected_range: tuple[float, float] | None = (report.minimum, report.maximum)

    if metric is not None and value is not None:
        label = _METRIC_LABELS.get(metric, field)
        dir_str = _direction(value, report.minimum, report.maximum)
        code = f"{field}_{dir_str}"
        message = (
            f"{label} is {dir_str.replace('_', ' ')}: "
            f"{value} (expected {report.minimum}-{report.maximum})"
        )
    else:
        code = f"{field}_out_of_range"
        message = f"{field} is out of range"

    return Problem(
        code=code,
        message=message,
        severity=severity,
        metric=metric,
        value=value,
        expected_range=expected_range,
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
            ``"orp_too_low"``.
        message: Human-readable description of the problem.
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


def detect_problems(pool_state: PoolState) -> list[Problem]:
    """Detect all chemistry problems present in a pool state snapshot.

    Iterates over every parameter in :attr:`~.model.PoolState.chemistry_report`
    and returns a :class:`Problem` for each one whose status is not
    :attr:`~.model.ChemistryStatus.GOOD`.

    The function is resilient to missing data: ``None`` readings are skipped,
    and any unexpected error while evaluating a single parameter is logged and
    skipped rather than propagated.

    The result is ordered from most to least severe
    (:attr:`Severity.CRITICAL` first, then :attr:`Severity.MEDIUM`, then
    :attr:`Severity.LOW`).

    Args:
        pool_state: The current pool state snapshot produced by the coordinator.

    Returns:
        A list of :class:`Problem` instances, empty when all parameters are
        within acceptable ranges or no readings are available.

    Example::

        state = coordinator.data
        problems = detect_problems(state)
        for problem in problems:
            print(f"[{problem.severity}] {problem.code}: {problem.message}")
    """
    report = pool_state.chemistry_report
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
            problems.append(_make_problem(field, param_report))
        except Exception:
            _LOGGER.exception("Unexpected error while building Problem for field %r", field)

    problems.sort(key=lambda p: _SEVERITY_ORDER[p.severity])
    return problems
