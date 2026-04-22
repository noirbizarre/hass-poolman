"""Salt level rule (salt electrolysis pools only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...chemistry import SALT_MAX, SALT_MIN
from ...model import PoolMode, TreatmentType
from ...problem import MetricName, Problem, Severity
from ..base import Rule, RuleResult

if TYPE_CHECKING:
    from ...model import PoolState


class SaltRule(Rule):
    """Evaluate salt concentration for salt electrolysis pools (2700 - 3400 ppm).

    Only active when the pool treatment is
    :attr:`~...model.TreatmentType.SALT_ELECTROLYSIS`.  Requires
    :attr:`~...model.PoolState.pool` to be set; returns empty result when
    ``None``.

    - Below minimum → :attr:`~...problem.Severity.MEDIUM` (add salt)
    - Above maximum → :attr:`~...problem.Severity.LOW` (partial drain)

    Disabled in :attr:`~...model.PoolMode.WINTER_PASSIVE` and
    :attr:`~...model.PoolMode.WINTER_ACTIVE` modes.
    """

    id = "salt"
    description = "Evaluate salt concentration for salt electrolysis pools"

    def evaluate(self, state: PoolState) -> RuleResult:  # type: ignore[override]
        """Evaluate salt level and return a problem when out of range."""
        if state.pool is None:
            return RuleResult()
        if state.pool.treatment != TreatmentType.SALT_ELECTROLYSIS:
            return RuleResult()
        if (
            state.mode in (PoolMode.WINTER_PASSIVE, PoolMode.WINTER_ACTIVE)
            or state.reading.salt is None
        ):
            return RuleResult()

        salt = state.reading.salt

        if salt < SALT_MIN:
            return RuleResult(
                problems=[
                    Problem(
                        code="salt_too_low",
                        message=f"Salt level is too low: {salt:.0f} ppm (minimum {SALT_MIN} ppm)",
                        severity=Severity.MEDIUM,
                        metric=MetricName.SALT,
                        value=salt,
                        expected_range=(SALT_MIN, SALT_MAX),
                    )
                ]
            )

        if salt > SALT_MAX:
            return RuleResult(
                problems=[
                    Problem(
                        code="salt_too_high",
                        message=f"Salt level is too high: {salt:.0f} ppm (maximum {SALT_MAX} ppm)",
                        severity=Severity.LOW,
                        metric=MetricName.SALT,
                        value=salt,
                        expected_range=(SALT_MIN, SALT_MAX),
                    )
                ]
            )

        return RuleResult()
