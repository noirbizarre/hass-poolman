"""Calcium hardness rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import HARDNESS_MAX, HARDNESS_MIN, compute_hardness_adjustment
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule
from ._helpers import treatment_from_dosage

if TYPE_CHECKING:
    from ...model import PoolState


class HardnessRule(Rule):
    """Evaluate calcium hardness (150 - 400 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM` (add hardness increaser)
    - Above maximum → :attr:`~...problem.Severity.LOW` (no chemical fix; drain)

    For the low case, a :class:`~...recommendation.Treatment` is attached
    when :attr:`~...model.PoolState.pool` is set.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "hardness"
    description = "Evaluate calcium hardness"
    priority = 60

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate calcium hardness and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.hardness is None
        ):
            return []

        hardness = state.reading.hardness

        if hardness < HARDNESS_MIN:
            code = "hardness_too_low"
            dosage = (
                compute_hardness_adjustment(state.pool, state.reading)
                if state.pool is not None
                else None
            )
            return [
                Problem(
                    code=code,
                    message=(
                        f"Calcium hardness is too low: {hardness:.0f} ppm"
                        f" (minimum {HARDNESS_MIN} ppm)"
                    ),
                    severity=Severity.MEDIUM,
                    metric=MetricName.HARDNESS,
                    value=hardness,
                    expected_range=(HARDNESS_MIN, HARDNESS_MAX),
                    treatment=treatment_from_dosage(code, dosage),
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
