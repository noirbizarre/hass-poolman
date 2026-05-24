"""ORP / sanitizer level rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import ORP_MAX, ORP_MIN_ACCEPTABLE, compute_sanitizer_status
from ...model import ChemicalProduct, PoolMode
from ...problem import MetricName, Problem, Severity
from ...recommendation import Treatment
from ..base import Rule

if TYPE_CHECKING:
    from ...model import PoolState


class SanitizerRule(Rule):
    """Evaluate sanitizer effectiveness via ORP.

    Generates a :class:`~...problem.Problem` when ORP is outside the
    acceptable range (ORP_MIN_ACCEPTABLE - ORP_MAX).

    Requires :attr:`~...model.PoolState.pool` to determine the treatment
    type.  Returns an empty list when ``pool`` is ``None``.

    For the high-ORP case, a :class:`~...recommendation.Treatment` with
    :attr:`~...model.ChemicalProduct.NEUTRALIZER` is attached.  The low-ORP
    case has no specific product (operator is asked to increase sanitizer).

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "sanitizer"
    description = "Evaluate sanitizer effectiveness via ORP"
    priority = 40

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate sanitizer via ORP and return a problem when out of range."""
        if state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE):
            return []
        if state.pool is None or state.reading.orp is None:
            return []

        result = compute_sanitizer_status(state.reading, state.pool.treatment)
        if result is None:
            return []

        orp = state.reading.orp

        if orp > ORP_MAX:
            code = "orp_too_high"
            product_id = ChemicalProduct.NEUTRALIZER.value
            return [
                Problem(
                    code=code,
                    message=f"ORP is too high: {orp:.0f} mV (maximum {ORP_MAX} mV)",
                    severity=Severity.MEDIUM,
                    metric=MetricName.ORP,
                    value=orp,
                    expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
                    treatment=Treatment(
                        id=f"{code}_{product_id}",
                        product_id=product_id,
                        name=product_id.replace("_", " ").title(),
                        quantity=0.0,
                        unit="g",
                    ),
                )
            ]

        severity = Severity.CRITICAL if result.severity == Severity.CRITICAL else Severity.MEDIUM
        return [
            Problem(
                code="orp_too_low",
                message=(
                    f"ORP is too low: {orp:.0f} mV (minimum acceptable {ORP_MIN_ACCEPTABLE} mV)"
                ),
                severity=severity,
                metric=MetricName.ORP,
                value=orp,
                expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
            )
        ]
