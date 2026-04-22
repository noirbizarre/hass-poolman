"""Algae risk rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import ORP_MAX, ORP_MIN_ACCEPTABLE
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState

_ALGAE_TEMP_THRESHOLD = 28.0  # °C above which algae risk is elevated


class AlgaeRiskRule(Rule):
    """Detect high algae risk from warm water combined with low ORP.

    Fires a :attr:`~...problem.Severity.CRITICAL` problem when both:

    - Water temperature > 28 °C, **and**
    - ORP < minimum acceptable level.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "algae_risk"
    description = "Detect algae risk from warm water and low ORP"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate algae risk and return a critical problem when conditions are met."""
        if state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE):
            return RuleResult()

        if state.reading.temp_c is None or state.reading.orp is None:
            return RuleResult()

        if state.reading.temp_c > _ALGAE_TEMP_THRESHOLD and state.reading.orp < ORP_MIN_ACCEPTABLE:
            return RuleResult(
                problems=[
                    Problem(
                        code="algae_risk",
                        message=(
                            f"High algae risk: water temperature {state.reading.temp_c:.1f} °C"
                            f" with ORP {state.reading.orp:.0f} mV"
                        ),
                        severity=Severity.CRITICAL,
                        metric=MetricName.ORP,
                        value=state.reading.orp,
                        expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
                    )
                ]
            )

        return RuleResult()
