"""pH deviation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import (
    PH_MAX,
    PH_MIN,
    PH_TARGET,
    PH_TOLERANCE,
    compute_ph_adjustment,
)
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule
from ._helpers import treatment_from_dosage

if TYPE_CHECKING:
    from ...model import PoolState


class PhRule(Rule):
    """Detect pH deviation from the target range (6.8 - 7.8, target 7.2).

    Severity levels:

    - Outside min-max (< 6.8 or > 7.8) → :attr:`~...problem.Severity.CRITICAL`
    - Delta > 3 x tolerance → :attr:`~...problem.Severity.MEDIUM`
    - Delta > tolerance → :attr:`~...problem.Severity.LOW`

    When :attr:`~...model.PoolState.pool` is set, the rule also pre-computes a
    :class:`~...recommendation.Treatment` (pH+ or pH-) and attaches it to the
    produced :class:`~...problem.Problem` for downstream recommendation
    generation.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` mode.
    """

    id = "ph"
    description = "Detect pH deviation from target range"
    priority = 20

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate pH level and return a problem when out of range."""
        if state.mode == PoolMode.WINTER_PASSIVE or state.reading.ph is None:
            return []

        ph = state.reading.ph
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

        dosage = (
            compute_ph_adjustment(state.pool, state.reading) if state.pool is not None else None
        )
        treatment = treatment_from_dosage(code, dosage)

        return [
            Problem(
                code=code,
                message=message,
                severity=severity,
                metric=MetricName.PH,
                value=ph,
                expected_range=(PH_MIN, PH_MAX),
                treatment=treatment,
            )
        ]
