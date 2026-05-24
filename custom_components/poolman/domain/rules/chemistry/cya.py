"""Cyanuric acid (CYA / stabilizer) rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import CYA_MAX, CYA_MIN, compute_cya_adjustment
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule
from ._helpers import treatment_from_dosage

if TYPE_CHECKING:
    from ...model import PoolState


class CyaRule(Rule):
    """Evaluate cyanuric acid (stabilizer) concentration (20 - 75 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM` (add stabilizer)
    - Above maximum → :attr:`~...problem.Severity.LOW` (no chemical fix; drain)

    For the low case, a :class:`~...recommendation.Treatment` is attached
    when :attr:`~...model.PoolState.pool` is set.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "cya"
    description = "Evaluate cyanuric acid (stabilizer) concentration"
    priority = 50

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate CYA level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.cya is None
        ):
            return []

        cya = state.reading.cya

        if cya < CYA_MIN:
            code = "cya_too_low"
            dosage = (
                compute_cya_adjustment(state.pool, state.reading)
                if state.pool is not None
                else None
            )
            return [
                Problem(
                    code=code,
                    message=f"CYA is too low: {cya:.0f} ppm (minimum {CYA_MIN} ppm)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.CYA,
                    value=cya,
                    expected_range=(CYA_MIN, CYA_MAX),
                    treatment=treatment_from_dosage(code, dosage),
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
