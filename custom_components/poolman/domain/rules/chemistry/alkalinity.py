"""Total alkalinity (TAC) rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import TAC_MAX, TAC_MIN
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class TacRule(Rule):
    """Evaluate total alkalinity (TAC) level (80 - 150 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM`
    - Above maximum → :attr:`~...problem.Severity.LOW`

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "alkalinity"
    description = "Evaluate total alkalinity (TAC) level"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate TAC level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.tac is None
        ):
            return RuleResult()

        tac = state.reading.tac

        if tac < TAC_MIN:
            return RuleResult(
                problems=[
                    Problem(
                        code="alkalinity_too_low",
                        message=(
                            f"Total alkalinity is too low: {tac:.0f} ppm (minimum {TAC_MIN} ppm)"
                        ),
                        severity=Severity.MEDIUM,
                        metric=MetricName.ALKALINITY,
                        value=tac,
                        expected_range=(TAC_MIN, TAC_MAX),
                    )
                ]
            )

        if tac > TAC_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="alkalinity_too_high",
                        message=(
                            f"Total alkalinity is too high: {tac:.0f} ppm (maximum {TAC_MAX} ppm)"
                        ),
                        severity=Severity.LOW,
                        metric=MetricName.ALKALINITY,
                        value=tac,
                        expected_range=(TAC_MIN, TAC_MAX),
                    )
                ]
            )

        return RuleResult()
