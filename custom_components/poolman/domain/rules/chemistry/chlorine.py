"""Free chlorine level rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import (
    FREE_CHLORINE_MAX,
    FREE_CHLORINE_MIN,
    compute_free_chlorine_adjustment,
)
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule
from ._helpers import treatment_from_dosage

if TYPE_CHECKING:
    from ...model import PoolState


class FreeChlorineRule(Rule):
    """Evaluate free chlorine concentration (ppm).

    - Below minimum (< 1 ppm) → :attr:`~...problem.Severity.CRITICAL`
    - Above maximum (> 3 ppm) → :attr:`~...problem.Severity.LOW`

    For the low-chlorine case, the rule pre-computes a
    :class:`~...recommendation.Treatment` (shock chlorine) via
    :func:`~...chemistry.compute_free_chlorine_adjustment` and attaches it to
    the produced :class:`~...problem.Problem`.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "free_chlorine"
    description = "Evaluate free chlorine concentration"
    priority = 40

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate free chlorine level and return a problem when out of range."""
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.free_chlorine is None
        ):
            return []

        fc = state.reading.free_chlorine

        if fc < FREE_CHLORINE_MIN:
            code = "chlorine_too_low"
            dosage = compute_free_chlorine_adjustment(state.reading)
            return [
                Problem(
                    code=code,
                    message=(
                        f"Free chlorine is too low: {fc:.1f} ppm (minimum {FREE_CHLORINE_MIN} ppm)"
                    ),
                    severity=Severity.CRITICAL,
                    metric=MetricName.CHLORINE,
                    value=fc,
                    expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                    treatment=treatment_from_dosage(code, dosage),
                )
            ]

        if fc > FREE_CHLORINE_MAX:
            code = "chlorine_too_high"
            dosage = compute_free_chlorine_adjustment(state.reading)
            return [
                Problem(
                    code=code,
                    message=(
                        f"Free chlorine is too high: {fc:.1f} ppm (maximum {FREE_CHLORINE_MAX} ppm)"
                    ),
                    severity=Severity.LOW,
                    metric=MetricName.CHLORINE,
                    value=fc,
                    expected_range=(FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
                    treatment=treatment_from_dosage(code, dosage),
                )
            ]

        return []
