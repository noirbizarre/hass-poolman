"""Calcium hardness rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import HARDNESS_MAX, HARDNESS_MIN
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class HardnessRule(Rule):
    """Evaluate calcium hardness (150 - 400 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM` (add hardness increaser)
    - Above maximum → :attr:`~...problem.Severity.LOW` (no chemical fix; drain)

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "hardness"
    description = "Evaluate calcium hardness"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate calcium hardness and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.hardness is None
        ):
            return RuleResult()

        hardness = state.reading.hardness

        if hardness < HARDNESS_MIN:
            return RuleResult(
                problems=[
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
            )

        if hardness > HARDNESS_MAX:
            return RuleResult(
                problems=[
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
            )

        return RuleResult()
