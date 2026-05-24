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

    Rules are sorted by :attr:`~.base.Rule.priority` (ascending) at engine
    construction.  All detected :class:`~..problem.Problem` objects are then
    collected and the final list is sorted by :class:`~..problem.Severity`
    (critical first).

    Example::

        engine = RuleEngine(ALL_RULES)
        problems = engine.evaluate(state)
        for problem in problems:
            print(f"[{problem.severity}] {problem.code}: {problem.message}")

    Attributes:
        rules: The list of rules evaluated on each call to :meth:`evaluate`,
            sorted by :attr:`~.base.Rule.priority`.
    """

    def __init__(self, rules: list[Rule]) -> None:
        """Initialize the engine with a list of rules.

        Args:
            rules: List of :class:`~.base.Rule` instances to run.  The
                engine sorts them by :attr:`~.base.Rule.priority` (ascending)
                so call order is independent of the argument order.
        """
        self.rules = sorted(rules, key=lambda r: r.priority)

    def evaluate(self, state: PoolState) -> list[Problem]:
        """Run all rules and return detected problems sorted by severity.

        Args:
            state: Current pool state snapshot.

        Returns:
            All problems from all rules, sorted critical-first.  The sort is
            stable, so equal-severity problems retain the rule-priority
            order in which they were produced.
        """
        problems: list[Problem] = []
        for rule in self.rules:
            problems.extend(rule.evaluate(state))
        problems.sort(key=lambda p: _SEVERITY_ORDER.get(p.severity, 99))
        return problems
