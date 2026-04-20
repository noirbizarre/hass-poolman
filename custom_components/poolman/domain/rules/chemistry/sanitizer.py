"""ORP / sanitizer level rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import ORP_MAX, ORP_MIN_ACCEPTABLE, compute_sanitizer_status
from ...model import PoolMode
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class SanitizerRule(Rule):
    """Evaluate sanitizer effectiveness via ORP.

    Generates a :class:`~...problem.Problem` when ORP is outside the
    acceptable range (ORP_MIN_ACCEPTABLE - ORP_MAX).

    Requires :attr:`~...model.PoolState.pool` to determine the treatment
    type.  Returns an empty :class:`~..base.RuleResult` when ``pool`` is
    ``None``.

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "sanitizer"
    description = "Evaluate sanitizer effectiveness via ORP"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate sanitizer via ORP and return a problem when out of range."""
        if state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE):
            return RuleResult()
        if state.pool is None or state.reading.orp is None:
            return RuleResult()

        result = compute_sanitizer_status(state.reading, state.pool.treatment)
        if result is None:
            return RuleResult()

        orp = state.reading.orp

        if orp > ORP_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="orp_too_high",
                        message=f"ORP is too high: {orp:.0f} mV (maximum {ORP_MAX} mV)",
                        severity=Severity.MEDIUM,
                        metric=MetricName.ORP,
                        value=orp,
                        expected_range=(ORP_MIN_ACCEPTABLE, ORP_MAX),
                    )
                ]
            )

        severity = Severity.CRITICAL if result.severity == Severity.CRITICAL else Severity.MEDIUM
        return RuleResult(
            problems=[
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
        )
