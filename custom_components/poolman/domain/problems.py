"""Problem detection for pool chemistry.

This module provides a normalized :class:`Problem` representation for abnormal
chemistry metrics and the :func:`detect_problems` function that derives a list
of problems from a :class:`~.model.PoolState` snapshot.

No treatment logic is included here — problems only describe *what* is wrong,
not *how* to fix it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import ChemistryStatus, ParameterReport, PoolState, Severity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PARAMETER_LABELS: dict[str, str] = {
    "ph": "pH",
    "orp": "ORP",
    "free_chlorine": "free chlorine",
    "tds": "TDS",
    "salt": "salt",
    "tac": "TAC",
    "cya": "CYA",
    "hardness": "hardness",
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


def _make_problem(metric: str, report: ParameterReport) -> Problem:
    """Build a :class:`Problem` from a parameter name and its report.

    Args:
        metric: The parameter name (e.g. ``"ph"``, ``"orp"``).
        report: The evaluated :class:`ParameterReport` for that parameter.

    Returns:
        A fully populated :class:`Problem` instance.
    """
    label = _PARAMETER_LABELS.get(metric, metric)
    dir_str = _direction(report.value, report.minimum, report.maximum)
    severity = _severity_for(report)

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

    Attributes:
        code: Machine-readable identifier, e.g. ``"ph_too_high"`` or
            ``"orp_too_low"``.
        message: Human-readable description of the problem.
        severity: How serious the deviation is
            (:attr:`Severity.LOW`, :attr:`Severity.MEDIUM`, or
            :attr:`Severity.CRITICAL`).
        metric: The chemistry parameter name, e.g. ``"ph"`` or ``"orp"``.
        value: The actual measured value that triggered the problem.
        expected_range: ``(minimum, maximum)`` tuple representing the
            acceptable range for this parameter.
    """

    code: str
    message: str
    severity: Severity
    metric: str
    value: float
    expected_range: tuple[float, float]


def detect_problems(pool_state: PoolState) -> list[Problem]:
    """Detect all chemistry problems present in a pool state snapshot.

    Iterates over every parameter in :attr:`~.model.PoolState.chemistry_report`
    and returns a :class:`Problem` for each one whose status is not
    :attr:`~.model.ChemistryStatus.GOOD`.

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

    _severity_order = {Severity.CRITICAL: 0, Severity.MEDIUM: 1, Severity.LOW: 2}

    problems: list[Problem] = []
    for metric in report.model_fields:
        param_report: ParameterReport | None = getattr(report, metric)
        if param_report is None:
            continue
        if param_report.status == ChemistryStatus.GOOD:
            continue
        problems.append(_make_problem(metric, param_report))

    problems.sort(key=lambda p: _severity_order[p.severity])
    return problems
