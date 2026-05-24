"""Analysis pipeline orchestration for pool management.

This module provides the formal entry point for evaluating a pool state
and producing a structured diagnostic result.  It is the canonical home
for:

- :class:`AnalysisResult` -- the output of a full analysis run, bundling
  detected problems and generated recommendations with a timestamp.
- :func:`analyze_pool` -- pure orchestration function:
  ``PoolState → AnalysisResult``.
- :func:`generate_recommendations` -- derives
  :class:`~.recommendation.Recommendation` objects from a list of
  :class:`~.problem.Problem` objects.  Depends only on the problem list;
  any required dosage information is carried on
  :attr:`~.problem.Problem.treatment` by the rule that produced the
  problem.

Pipeline
--------

.. code-block:: text

    PoolState
        │
        ▼
    RuleEngine(ALL_RULES).evaluate(state)  ← domain/rules/
        │  list[Problem]  (each may carry a pre-computed Treatment)
        ▼
    generate_recommendations(problems)
        │  list[Recommendation]
        ▼
    AnalysisResult(problems, recommendations, timestamp)

Design constraints
------------------
- Pure functions only: stateless, deterministic, no side effects.
- No Home Assistant dependency anywhere in this module.
- :func:`generate_recommendations` depends **only** on
  :class:`~.problem.Problem` instances — no sensor or pool data.
- Resilient to missing / ``None`` sensor values — rules guard individually.

Example::

    from custom_components.poolman.domain.analysis import analyze_pool

    result = analyze_pool(pool_state)
    for problem in result.problems:
        print(f"[{problem.severity}] {problem.code}")
    for rec in result.recommendations:
        print(f"  → {rec.title}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .problem import Problem, Severity
from .recommendation import (
    ActionKind,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)
from .rules import ALL_RULES, RuleEngine

if TYPE_CHECKING:
    from .model import PoolState


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

# Map Severity → RecommendationPriority
_SEVERITY_TO_PRIORITY: dict[Severity, RecommendationPriority] = {
    Severity.LOW: RecommendationPriority.LOW,
    Severity.MEDIUM: RecommendationPriority.MEDIUM,
    Severity.CRITICAL: RecommendationPriority.CRITICAL,
}

# Map Severity → ActionKind (CRITICAL and MEDIUM problems are requirements)
_SEVERITY_TO_KIND: dict[Severity, ActionKind] = {
    Severity.LOW: ActionKind.SUGGESTION,
    Severity.MEDIUM: ActionKind.REQUIREMENT,
    Severity.CRITICAL: ActionKind.REQUIREMENT,
}

# Map problem code → (RecommendationType, title, description template).
# ``description`` may contain a ``{value}`` placeholder filled with
# :attr:`~.problem.Problem.value`.  Treatment quantity / product is carried
# on :attr:`~.problem.Problem.treatment`, **not** in this table.
_PROBLEM_RECOMMENDATIONS: dict[str, tuple[RecommendationType, str, str]] = {
    "ph_too_high": (
        RecommendationType.CHEMISTRY,
        "Lower pH",
        "pH is too high ({value}). Add pH- to bring it back to the target range.",
    ),
    "ph_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise pH",
        "pH is too low ({value}). Add pH+ to bring it back to the target range.",
    ),
    "orp_too_low": (
        RecommendationType.CHEMISTRY,
        "Increase sanitizer",
        "ORP is too low ({value} mV). Sanitizer effectiveness may be insufficient.",
    ),
    "orp_too_high": (
        RecommendationType.ALERT,
        "Reduce sanitizer",
        "ORP is too high ({value} mV). Reduce sanitizer dosage.",
    ),
    "chlorine_too_low": (
        RecommendationType.CHEMISTRY,
        "Add chlorine",
        "Free chlorine is too low ({value} ppm). Add shock chlorine.",
    ),
    "chlorine_too_high": (
        RecommendationType.ALERT,
        "Reduce chlorine",
        "Free chlorine is too high ({value} ppm). Reduce chlorine dosage.",
    ),
    "alkalinity_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise alkalinity",
        "Total alkalinity is too low ({value} ppm). Add TAC+ to raise it.",
    ),
    "alkalinity_too_high": (
        RecommendationType.ALERT,
        "Lower alkalinity",
        "Total alkalinity is too high ({value} ppm). pH- treatments will help lower it.",
    ),
    "cya_too_low": (
        RecommendationType.CHEMISTRY,
        "Add stabilizer",
        "Cyanuric acid is too low ({value} ppm). Add stabilizer to protect chlorine from UV.",
    ),
    "cya_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Cyanuric acid is too high ({value} ppm). No chemical can lower CYA; drain partially.",
    ),
    "hardness_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise calcium hardness",
        "Calcium hardness is too low ({value} ppm). Add calcium hardness increaser.",
    ),
    "hardness_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Calcium hardness is too high ({value} ppm). No chemical can lower hardness;"
        " drain partially.",
    ),
    "salt_too_low": (
        RecommendationType.CHEMISTRY,
        "Add salt",
        "Salt level is too low ({value} ppm). Add pool salt to reach the target.",
    ),
    "salt_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Salt level is too high ({value} ppm). Drain partially to dilute.",
    ),
    "tds_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "TDS is too high ({value} ppm). Drain partially to reduce dissolved solids.",
    ),
    "tds_too_low": (
        RecommendationType.MAINTENANCE,
        "Verify EC sensor calibration",
        "TDS is unusually low ({value} ppm). Check EC sensor calibration.",
    ),
    "_calibration": (
        RecommendationType.MAINTENANCE,
        "Calibrate sensor",
        "Sensor reading differs significantly from last manual measurement ({value}). Recalibrate.",
    ),
    "filtration_required": (
        RecommendationType.FILTRATION,
        "Run filtration",
        "Filtration is required for {value} hours today.",
    ),
    "algae_risk": (
        RecommendationType.ALERT,
        "High algae risk",
        "Water temperature is high and ORP is low ({value} mV). Risk of algae growth.",
    ),
}


_PRIORITY_ORDER: dict[RecommendationPriority, int] = {
    RecommendationPriority.CRITICAL: 0,
    RecommendationPriority.HIGH: 1,
    RecommendationPriority.MEDIUM: 2,
    RecommendationPriority.LOW: 3,
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def generate_recommendations(problems: list[Problem]) -> list[Recommendation]:
    """Derive :class:`~.recommendation.Recommendation` objects from problems.

    Pure :class:`~.problem.Problem` → :class:`~.recommendation.Recommendation`
    mapping.  No sensor reading or pool configuration is consulted: any
    dosage information must already be present on
    :attr:`~.problem.Problem.treatment` (rules attach it when the dosage is
    known).

    For each :class:`~.problem.Problem` the function:

    - Looks up the matching template (type, title, description) by
      :attr:`~.problem.Problem.code`.  Codes starting with ``"calibration_"``
      share the generic ``_calibration`` template.
    - Sets :class:`~.recommendation.RecommendationPriority` and
      :class:`~.recommendation.ActionKind` from :attr:`~.problem.Problem.severity`
      (``CRITICAL`` / ``MEDIUM`` → ``REQUIREMENT``, ``LOW`` → ``SUGGESTION``).
    - Carries :attr:`~.problem.Problem.treatment` (when present) into the
      :attr:`~.recommendation.Recommendation.treatments` list.

    Problems with no matching template are silently skipped (forward
    compatibility: new problem codes added before new templates exist will
    not crash the pipeline).

    Duplicate recommendations for the same problem code are deduplicated;
    only the highest-severity one is kept.

    Args:
        problems: List of :class:`~.problem.Problem` objects produced by the
            rule engine.

    Returns:
        List of :class:`~.recommendation.Recommendation` objects, sorted by
        priority (critical first).
    """
    # Deduplicate: keep highest-severity problem per code
    seen: dict[str, Problem] = {}
    for problem in problems:
        existing = seen.get(problem.code)
        if existing is None or list(Severity).index(problem.severity) > list(Severity).index(
            existing.severity
        ):
            seen[problem.code] = problem

    recommendations: list[Recommendation] = []
    for code, problem in seen.items():
        # Calibration codes are dynamic; map them to a generic MAINTENANCE template
        lookup_code = code if not code.startswith("calibration_") else "_calibration"
        template = _PROBLEM_RECOMMENDATIONS.get(lookup_code)
        if template is None:
            continue

        rec_type, title, desc_template = template
        priority = _SEVERITY_TO_PRIORITY[problem.severity]
        kind = _SEVERITY_TO_KIND[problem.severity]

        description = desc_template.format(
            value=problem.value if problem.value is not None else "N/A",
        )

        treatments = [problem.treatment] if problem.treatment is not None else []
        related = [problem.metric] if problem.metric is not None else []

        recommendations.append(
            Recommendation(
                id=f"rec_{code}",
                type=rec_type,
                severity=problem.severity,
                priority=priority,
                kind=kind,
                title=title,
                description=description,
                reason=code,
                treatments=treatments,
                related_metrics=related,
            )
        )

    recommendations.sort(key=lambda r: _PRIORITY_ORDER.get(r.priority, 99))
    return recommendations


@dataclass(frozen=True)
class AnalysisResult:
    """The output of a full pool analysis run.

    Bundles the detected :class:`~.problem.Problem` objects and the derived
    :class:`~.recommendation.Recommendation` objects produced in a single
    pipeline execution, together with the timestamp of the run.

    Attributes:
        problems: All water-quality problems detected from the pool state
            snapshot, ordered from most to least severe.
        recommendations: Actionable recommendations derived from the
            problems, ordered from most to least urgent.
        timestamp: UTC timestamp of when this analysis was performed.
    """

    problems: list[Problem] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


def analyze_pool(state: PoolState) -> AnalysisResult:
    """Run the full pool analysis pipeline.

    Pure, deterministic, stateless function.  Takes a pool state snapshot
    and returns an :class:`AnalysisResult` containing all detected problems
    and recommendations.

    Pipeline steps:

    1. Run :class:`~.rules.RuleEngine` with :data:`~.rules.ALL_RULES` to
       produce a list of :class:`~.problem.Problem` objects.  Rules attach
       pre-computed :class:`~.recommendation.Treatment` instances to
       problems when a dosage is known.
    2. Call :func:`generate_recommendations` to derive a list of
       :class:`~.recommendation.Recommendation` objects from the problems
       alone (no sensor / pool re-reading).
    3. Return an :class:`AnalysisResult` with both lists and the current
       UTC timestamp.

    Args:
        state: The current pool state snapshot.  All sensor readings may be
            ``None``; the rules handle missing data gracefully.

    Returns:
        An :class:`AnalysisResult` with problems, recommendations, and
        timestamp populated.

    Example::

        result = analyze_pool(coordinator.data)
        if result.problems:
            print(f"{len(result.problems)} problem(s) detected")
        for rec in result.recommendations:
            print(f"  [{rec.priority}] {rec.title}: {rec.description}")
    """
    problems = RuleEngine(ALL_RULES).evaluate(state)
    recommendations = generate_recommendations(problems)
    return AnalysisResult(
        problems=problems,
        recommendations=recommendations,
        timestamp=datetime.now(UTC),
    )
