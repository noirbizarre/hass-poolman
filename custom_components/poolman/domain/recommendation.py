"""Structured recommendation types for pool management.

This module defines the types used to represent actionable recommendations
produced by the analysis pipeline.  It is the canonical home for:

- :class:`RecommendationType` -- what category of action is needed.
- :class:`RecommendationPriority` -- how urgent the recommendation is.
- :class:`ActionKind` -- whether the action is optional or mandatory.
- :class:`Treatment` -- a concrete chemical treatment step with quantity and
  unit.
- :class:`Recommendation` -- a fully structured recommendation referencing one
  or more :class:`Treatment` steps.

Relationship to other modules
------------------------------
- :mod:`.problem` defines :class:`~.problem.Problem` (what is wrong).
- This module defines :class:`Recommendation` (what to do about it).
- :mod:`.analysis` orchestrates the pipeline and produces an
  :class:`~.analysis.AnalysisResult` that bundles both.
- :mod:`.action` defines :class:`~.action.Action` (what the user actually did).

No Home Assistant dependency is present in this module.

Example::

    from custom_components.poolman.domain.recommendation import (
        Recommendation,
        RecommendationType,
        RecommendationPriority,
        ActionKind,
        Treatment,
    )

    rec = Recommendation(
        id="add_ph_minus",
        type=RecommendationType.CHEMISTRY,
        severity=Severity.MEDIUM,
        priority=RecommendationPriority.HIGH,
        kind=ActionKind.REQUIREMENT,
        title="Lower pH",
        description="pH is too high. Add pH- to bring it back to target.",
        reason="ph_too_high",
        treatments=[
            Treatment(
                id="ph_minus_300g",
                product_id="ph_minus",
                name="pH-",
                quantity=300.0,
                unit="g",
            )
        ],
        related_metrics=["ph"],
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum

from .problem import MetricName, Severity


class RecommendationType(StrEnum):
    """Category of a pool recommendation.

    Attributes:
        CHEMISTRY: Add or adjust a chemical product (pH, chlorine, etc.).
        FILTRATION: Run or adjust the filtration system.
        ALERT: Warning about a risky condition with no single chemical fix
            (e.g., algae risk, high TDS).
        MAINTENANCE: General maintenance action such as sensor recalibration
            or equipment check.
    """

    CHEMISTRY = "chemistry"
    FILTRATION = "filtration"
    ALERT = "alert"
    MAINTENANCE = "maintenance"


class RecommendationPriority(StrEnum):
    """Priority level for a recommendation.

    Determines urgency and which binary sensors it activates:

    - :attr:`LOW` and :attr:`MEDIUM` set ``action_required`` but not
      ``water_ok = False``.
    - :attr:`HIGH` and :attr:`CRITICAL` set both ``action_required`` and
      ``water_ok = False``.

    Attributes:
        LOW: Informational; no immediate action required.
        MEDIUM: Attention recommended in the near term.
        HIGH: Act soon to keep the pool safe and functional.
        CRITICAL: Immediate action required.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionKind(StrEnum):
    """Whether a recommendation is optional or mandatory.

    Attributes:
        SUGGESTION: An optional improvement that would bring parameters
            closer to ideal.  The pool is still functional without it.
        REQUIREMENT: The pool needs this action to remain safe or
            functional.
    """

    SUGGESTION = "suggestion"
    REQUIREMENT = "requirement"


@dataclass(frozen=True)
class Treatment:
    """A concrete chemical treatment step within a recommendation.

    Represents a single product application: what product, how much, and
    in which unit.  One :class:`Recommendation` may contain multiple
    :class:`Treatment` steps (e.g., add pH- first, then re-test).

    Attributes:
        id: Unique identifier for this treatment step, e.g.
            ``"ph_minus_300g"``.
        product_id: Identifier of the chemical product from
            :class:`~.model.ChemicalProduct`, e.g. ``"ph_minus"``.
        name: Human-readable product name, e.g. ``"pH-"``.
        quantity: Amount of product to apply.
        unit: Unit for the quantity.  MUST be a Home Assistant-compatible
            unit string, e.g. ``"g"``, ``"mL"``, or ``"tablet"``.
        duration: Optional wait duration after applying this treatment
            before re-testing or proceeding to the next step.
    """

    id: str
    product_id: str
    name: str
    quantity: float
    unit: str  # HA-compatible unit: "g", "mL", "tablet", …
    duration: timedelta | None = None


@dataclass(frozen=True)
class Recommendation:
    """A fully structured pool management recommendation.

    Produced by the analysis pipeline after detecting one or more
    :class:`~.problem.Problem` objects.  Unlike the legacy
    :class:`~.model.Recommendation` Pydantic model, this dataclass carries
    a rich :attr:`treatments` list with HA-compatible units and explicit
    links back to the originating problems via :attr:`reason` and
    :attr:`related_metrics`.

    Attributes:
        id: Unique identifier for this recommendation, e.g.
            ``"lower_ph"``.
        type: What category of action is needed
            (:class:`RecommendationType`).
        severity: How serious the underlying problem is
            (:class:`~.problem.Severity`).
        priority: Urgency level (:class:`RecommendationPriority`).
        kind: Whether the action is optional or mandatory
            (:class:`ActionKind`).
        title: Short human-readable title, e.g. ``"Lower pH"``.
        description: Full human-readable description including current
            reading and target range.
        reason: Problem :attr:`~.problem.Problem.code` that triggered this
            recommendation, e.g. ``"ph_too_high"``.
        treatments: Ordered list of concrete :class:`Treatment` steps to
            resolve the problem.  May be empty for alert-type
            recommendations where no specific product is required.
        related_metrics: List of :class:`~.problem.MetricName` values that
            this recommendation addresses.
    """

    id: str
    type: RecommendationType
    severity: Severity
    priority: RecommendationPriority
    kind: ActionKind
    title: str
    description: str
    reason: str
    treatments: list[Treatment] = field(default_factory=list)
    related_metrics: list[MetricName] = field(default_factory=list)
