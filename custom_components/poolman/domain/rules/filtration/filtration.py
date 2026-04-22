"""Filtration duration rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...filtration import compute_filtration_duration
from ...model import PoolMode
from ...problem import Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class FiltrationRule(Rule):
    """Signal that filtration is needed based on temperature and pool config.

    Requires :attr:`~...model.PoolState.pool` to be set; returns empty result
    when ``None``.

    Severity scales with required duration:

    - ≥ 12 hours → :attr:`~...problem.Severity.MEDIUM`
    - < 12 hours → :attr:`~...problem.Severity.LOW`

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` mode.
    """

    id = "filtration"
    description = "Signal required filtration duration"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate filtration needs and return a problem when action is due."""
        if state.mode == PoolMode.WINTER_PASSIVE:
            return RuleResult()
        if state.pool is None:
            return RuleResult()

        hours = compute_filtration_duration(state.pool, state.reading, state.mode)
        if hours is None:
            return RuleResult()

        severity = Severity.MEDIUM if hours >= 12 else Severity.LOW
        return RuleResult(
            problems=[
                Problem(
                    code="filtration_required",
                    message=f"Run filtration for {hours:.1f} hours today",
                    severity=severity,
                    metric=None,
                    value=hours,
                    expected_range=None,
                )
            ]
        )
