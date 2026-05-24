"""Base types for the pool rule engine.

Defines the :class:`Rule` abstract base class.  Each concrete rule evaluates
one aspect of the pool state and returns a list of :class:`~..problem.Problem`
objects.

Design constraints
------------------
- Rules are pure functions: stateless, deterministic, no side effects.
- Rules receive the full :class:`~..model.PoolState` and extract what they need.
- Rules may attach a pre-computed :class:`~..recommendation.Treatment` to a
  :class:`~..problem.Problem` so that downstream recommendation generation
  does not need to re-read sensor or pool data.
- No Home Assistant dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..problem import Problem

if TYPE_CHECKING:
    from ..model import PoolState


class Rule(ABC):
    """Abstract base class for pool management rules.

    Each concrete rule evaluates one aspect of the pool state and returns a
    list of :class:`~..problem.Problem` describing any detected issues.

    Rules must be:

    - **Stateless** — no instance state mutated during evaluation.
    - **Deterministic** — same input always produces same output.
    - **Side-effect free** — no I/O, no logging, no HA calls.

    Attributes:
        id: Unique machine-readable identifier, e.g. ``"ph"``.
        description: Short human-readable description of what the rule checks.
        priority: Execution order hint (lower runs first).  Defaults to
            ``100``.  The :class:`~.engine.RuleEngine` sorts rules by this
            value before evaluating them; the final list of problems is then
            re-sorted by :class:`~..problem.Severity`, so ``priority`` is
            mostly observable for equal-severity problems where the stable
            sort preserves rule order.
    """

    id: str
    description: str
    priority: int = 100

    @abstractmethod
    def evaluate(self, state: PoolState) -> list[Problem]:
        """Evaluate the rule against the current pool state.

        Args:
            state: Full pool state snapshot. Rules extract only the fields
                they need (``state.reading``, ``state.mode``, ``state.pool``,
                etc.).

        Returns:
            A list of zero or more detected :class:`~..problem.Problem`
            instances.  Each problem may carry a pre-computed
            :class:`~..recommendation.Treatment` via
            :attr:`~..problem.Problem.treatment`.
        """
