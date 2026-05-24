"""Total alkalinity (TAC) rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import TAC_MAX, TAC_MIN, compute_tac_adjustment
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule
from ._helpers import treatment_from_dosage

if TYPE_CHECKING:
    from ...model import PoolState


class TacRule(Rule):
    """Evaluate total alkalinity (TAC) level (80 - 150 ppm).

    - Below minimum → :attr:`~...problem.Severity.MEDIUM`
    - Above maximum → :attr:`~...problem.Severity.LOW`

    When :attr:`~...model.PoolState.pool` is set, the rule pre-computes a
    :class:`~...recommendation.Treatment` (TAC+ for low, pH- for high) and
    attaches it to the produced :class:`~...problem.Problem`.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "alkalinity"
    description = "Evaluate total alkalinity (TAC) level"
    priority = 30

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate TAC level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.tac is None
        ):
            return []

        tac = state.reading.tac
        dosage = (
            compute_tac_adjustment(state.pool, state.reading) if state.pool is not None else None
        )

        if tac < TAC_MIN:
            code = "alkalinity_too_low"
            return [
                Problem(
                    code=code,
                    message=(f"Total alkalinity is too low: {tac:.0f} ppm (minimum {TAC_MIN} ppm)"),
                    severity=Severity.MEDIUM,
                    metric=MetricName.ALKALINITY,
                    value=tac,
                    expected_range=(TAC_MIN, TAC_MAX),
                    treatment=treatment_from_dosage(code, dosage),
                )
            ]

        if tac > TAC_MAX:
            code = "alkalinity_too_high"
            return [
                Problem(
                    code=code,
                    message=(
                        f"Total alkalinity is too high: {tac:.0f} ppm (maximum {TAC_MAX} ppm)"
                    ),
                    severity=Severity.LOW,
                    metric=MetricName.ALKALINITY,
                    value=tac,
                    expected_range=(TAC_MIN, TAC_MAX),
                    treatment=treatment_from_dosage(code, dosage),
                )
            ]

        return []
