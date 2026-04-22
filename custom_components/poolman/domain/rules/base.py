"""Base types for the pool rule engine.

Defines the :class:`Rule` abstract base class and the :class:`RuleResult`
dataclass that every rule returns.

Design constraints
------------------
- Rules are pure functions: stateless, deterministic, no side effects.
- Rules receive the full :class:`~..model.PoolState` and extract what they need.
- No Home Assistant dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..problem import Problem

if TYPE_CHECKING:
    from ..model import PoolState


@dataclass
class RuleResult:
    """Output of a single rule evaluation.

    Attributes:
        problems: List of detected problems. Empty when the rule finds no issue.
    """

    problems: list[Problem] = field(default_factory=list)


class Rule(ABC):
    """Abstract base class for pool management rules.

    Each concrete rule evaluates one aspect of the pool state and returns a
    :class:`RuleResult` describing any detected issues.

    Rules must be:

    - **Stateless** — no instance state mutated during evaluation.
    - **Deterministic** — same input always produces same output.
    - **Side-effect free** — no I/O, no logging, no HA calls.

    Attributes:
        id: Unique machine-readable identifier, e.g. ``"ph"``.
        description: Short human-readable description of what the rule checks.
    """

    id: str
    description: str

    @abstractmethod
    def evaluate(self, state: PoolState) -> RuleResult:
        """Evaluate the rule against the current pool state.

        Args:
            state: Full pool state snapshot. Rules extract only the fields
                they need (``state.reading``, ``state.mode``, ``state.pool``,
                etc.).

        Returns:
            :class:`RuleResult` with zero or more detected problems.
        """
