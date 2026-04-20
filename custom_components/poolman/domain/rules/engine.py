"""Rule engine for pool management.

The :class:`RuleEngine` runs a list of :class:`~.base.Rule` instances against
a :class:`~..model.PoolState` snapshot, collects all detected
:class:`~..problem.Problem` objects, and returns them sorted by severity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..problem import Problem, Severity
from .base import Rule

if TYPE_CHECKING:
    from ..model import PoolState

_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
}


class RuleEngine:
    """Evaluates all registered rules against a pool state snapshot.

    Rules are evaluated in registration order. All detected
    :class:`~..problem.Problem` objects are collected and returned sorted
    by severity (critical first).

    Example::

        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(state)
        for problem in problems:
            print(f"[{problem.severity}] {problem.code}: {problem.message}")

    Attributes:
        rules: The list of rules evaluated on each call to :meth:`evaluate`.
    """

    def __init__(self, rules: list[Rule]) -> None:
        """Initialize the engine with a list of rules.

        Args:
            rules: Ordered list of :class:`~.base.Rule` instances to run.
        """
        self.rules = rules

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Run all rules and return detected problems sorted by severity.

        Args:
            state: Current pool state snapshot.

        Returns:
            All problems from all rules, sorted critical-first.
        """
        problems: list[Problem] = []
        for rule in self.rules:
            problems.extend(rule.evaluate(state).problems)
        problems.sort(key=lambda p: _SEVERITY_ORDER.get(p.severity, 99))
        return problems
