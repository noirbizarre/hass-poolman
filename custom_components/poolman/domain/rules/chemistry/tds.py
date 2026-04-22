"""Total Dissolved Solids (TDS) rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import TDS_MAX, TDS_MIN
from ...model import PoolMode, TreatmentType
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class TdsRule(Rule):
    """Evaluate Total Dissolved Solids (TDS) level.

    Skipped for salt electrolysis pools (dissolved salt naturally raises TDS
    above freshwater thresholds).  Requires :attr:`~...model.PoolState.pool`;
    returns empty result when ``None``.

    - Above maximum → :attr:`~...problem.Severity.MEDIUM` (partial drain)
    - Below minimum → :attr:`~...problem.Severity.LOW` (check EC sensor)

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "tds"
    description = "Evaluate Total Dissolved Solids (TDS) level"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate TDS level and return a problem when out of range."""
        if state.pool is None:
            return RuleResult()
        # Salt electrolysis pools naturally have high TDS from dissolved salt
        if state.pool.treatment == TreatmentType.SALT_ELECTROLYSIS:
            return RuleResult()
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.tds is None
        ):
            return RuleResult()

        tds = state.reading.tds

        if tds > TDS_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="tds_too_high",
                        message=f"TDS is too high: {tds:.0f} ppm (maximum {TDS_MAX} ppm)",
                        severity=Severity.MEDIUM,
                        metric=MetricName.TDS,
                        value=tds,
                        expected_range=(TDS_MIN, TDS_MAX),
                    )
                ]
            )

        if tds < TDS_MIN:
            return RuleResult(
                problems=[
                    Problem(
                        code="tds_too_low",
                        message=f"TDS is unusually low: {tds:.0f} ppm (minimum {TDS_MIN} ppm)",
                        severity=Severity.LOW,
                        metric=MetricName.TDS,
                        value=tds,
                        expected_range=(TDS_MIN, TDS_MAX),
                    )
                ]
            )

        return RuleResult()
