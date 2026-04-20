"""Free chlorine level rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import FREE_CHLORINE_MAX, FREE_CHLORINE_MIN
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class FreeChlorineRule(Rule):
    """Evaluate free chlorine concentration (ppm).

    - Below minimum (< 1 ppm) → :attr:`~...problem.Severity.CRITICAL`
    - Above maximum (> 3 ppm) → :attr:`~...problem.Severity.LOW`

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "free_chlorine"
    description = "Evaluate free chlorine concentration"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate free chlorine level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.free_chlorine is None
        ):
            return RuleResult()

        fc = state.reading.free_chlorine

        if fc < FREE_CHLORINE_MIN:
            return RuleResult(
                problems=[
                    Problem(
                        code="chlorine_too_low",
                        message=(
                            f"Free chlorine is too low: {fc:.1f} ppm"
                            f" (minimum {FREE_CHLORINE_MIN} ppm)"
                        ),
                        severity=Severity.CRITICAL,
                        metric=MetricName.CHLORINE,
                        value=fc,
                        expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                    )
                ]
            )

        if fc > FREE_CHLORINE_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="chlorine_too_high",
                        message=(
                            f"Free chlorine is too high: {fc:.1f} ppm"
                            f" (maximum {FREE_CHLORINE_MAX} ppm)"
                        ),
                        severity=Severity.LOW,
                        metric=MetricName.CHLORINE,
                        value=fc,
                        expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                    )
                ]
            )

        return RuleResult()
