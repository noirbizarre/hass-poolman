"""Cyanuric acid (CYA / stabilizer) rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import CYA_MAX, CYA_MIN
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class CyaRule(Rule):
    """Evaluate cyanuric acid (stabilizer) concentration (20 - 75 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM` (add stabilizer)
    - Above maximum → :attr:`~...problem.Severity.LOW` (no chemical fix; drain)

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "cya"
    description = "Evaluate cyanuric acid (stabilizer) concentration"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate CYA level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.cya is None
        ):
            return RuleResult()

        cya = state.reading.cya

        if cya < CYA_MIN:
            return RuleResult(
                problems=[
                    Problem(
                        code="cya_too_low",
                        message=f"CYA is too low: {cya:.0f} ppm (minimum {CYA_MIN} ppm)",
                        severity=Severity.MEDIUM,
                        metric=MetricName.CYA,
                        value=cya,
                        expected_range=(CYA_MIN, CYA_MAX),
                    )
                ]
            )

        if cya > CYA_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="cya_too_high",
                        message=f"CYA is too high: {cya:.0f} ppm (maximum {CYA_MAX} ppm)",
                        severity=Severity.LOW,
                        metric=MetricName.CYA,
                        value=cya,
                        expected_range=(CYA_MIN, CYA_MAX),
                    )
                ]
            )

        return RuleResult()
