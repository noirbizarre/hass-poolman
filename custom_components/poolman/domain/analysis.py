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
  :class:`~.problem.Problem` objects.

Pipeline
--------

.. code-block:: text

    PoolState
        │
        ▼
    detect_problems()          ← domain/problem.py
        │  list[Problem]
        ▼
    generate_recommendations() ← domain/analysis.py (this module)
        │  list[Recommendation]
        ▼
    AnalysisResult(problems, recommendations, timestamp)

Design constraints
------------------
- Pure functions only: stateless, deterministic, no side effects.
- No Home Assistant dependency anywhere in this module.
- Resilient to missing / ``None`` sensor values — handled by
  :func:`~.problem.detect_problems`.

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

from .model import PoolState
from .problem import MetricName, Problem, Severity, detect_problems
from .recommendation import (
    ActionKind,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    Treatment,
)

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

# Map Severity → RecommendationPriority
_SEVERITY_TO_PRIORITY: dict[Severity, RecommendationPriority] = {
    Severity.LOW: RecommendationPriority.LOW,
    Severity.MEDIUM: RecommendationPriority.MEDIUM,
    Severity.CRITICAL: RecommendationPriority.CRITICAL,
}

# Map Severity → ActionKind (CRITICAL problems are always requirements)
_SEVERITY_TO_KIND: dict[Severity, ActionKind] = {
    Severity.LOW: ActionKind.SUGGESTION,
    Severity.MEDIUM: ActionKind.REQUIREMENT,
    Severity.CRITICAL: ActionKind.REQUIREMENT,
}

# Map problem code → (RecommendationType, title, description template, product_id, unit)
# ``description`` may contain ``{value}`` and ``{min}``/``{max}`` placeholders.
_PROBLEM_RECOMMENDATIONS: dict[
    str,
    tuple[RecommendationType, str, str, str | None, str | None],
] = {
    "ph_too_high": (
        RecommendationType.CHEMISTRY,
        "Lower pH",
        "pH is too high ({value}). Add pH- to bring it back to the target range.",
        "ph_minus",
        "g",
    ),
    "ph_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise pH",
        "pH is too low ({value}). Add pH+ to bring it back to the target range.",
        "ph_plus",
        "g",
    ),
    "orp_too_low": (
        RecommendationType.CHEMISTRY,
        "Increase sanitizer",
        "ORP is too low ({value} mV). Sanitizer effectiveness may be insufficient.",
        None,
        None,
    ),
    "orp_too_high": (
        RecommendationType.ALERT,
        "Reduce sanitizer",
        "ORP is too high ({value} mV). Reduce sanitizer dosage.",
        "neutralizer",
        "g",
    ),
    "chlorine_too_low": (
        RecommendationType.CHEMISTRY,
        "Add chlorine",
        "Free chlorine is too low ({value} ppm). Add shock chlorine.",
        "chlore_choc",
        "g",
    ),
    "chlorine_too_high": (
        RecommendationType.ALERT,
        "Reduce chlorine",
        "Free chlorine is too high ({value} ppm). Reduce chlorine dosage.",
        "neutralizer",
        "g",
    ),
    "alkalinity_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise alkalinity",
        "Total alkalinity is too low ({value} ppm). Add TAC+ to raise it.",
        "tac_plus",
        "g",
    ),
    "alkalinity_too_high": (
        RecommendationType.ALERT,
        "Lower alkalinity",
        "Total alkalinity is too high ({value} ppm). pH- treatments will help lower it.",
        "ph_minus",
        "g",
    ),
    "cya_too_low": (
        RecommendationType.CHEMISTRY,
        "Add stabilizer",
        "Cyanuric acid is too low ({value} ppm). Add stabilizer to protect chlorine from UV.",
        "stabilizer",
        "g",
    ),
    "cya_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Cyanuric acid is too high ({value} ppm). No chemical can lower CYA; drain partially.",
        None,
        None,
    ),
    "hardness_too_low": (
        RecommendationType.CHEMISTRY,
        "Raise calcium hardness",
        "Calcium hardness is too low ({value} ppm). Add calcium hardness increaser.",
        "calcium_hardness_increaser",
        "g",
    ),
    "hardness_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Calcium hardness is too high ({value} ppm). No chemical can lower hardness;"
        " drain partially.",
        None,
        None,
    ),
    "salt_too_low": (
        RecommendationType.CHEMISTRY,
        "Add salt",
        "Salt level is too low ({value} ppm). Add pool salt to reach the target.",
        "salt",
        "g",
    ),
    "salt_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "Salt level is too high ({value} ppm). Drain partially to dilute.",
        None,
        None,
    ),
    "tds_too_high": (
        RecommendationType.ALERT,
        "Partial water drain required",
        "TDS is too high ({value} ppm). Drain partially to reduce dissolved solids.",
        None,
        None,
    ),
    "tds_too_low": (
        RecommendationType.MAINTENANCE,
        "Verify EC sensor calibration",
        "TDS is unusually low ({value} ppm). Check EC sensor calibration.",
        None,
        None,
    ),
}

# Map MetricName to the problem code prefix used in _PROBLEM_RECOMMENDATIONS
_METRIC_TO_PROBLEM_PREFIX: dict[MetricName, str] = {
    MetricName.PH: "ph",
    MetricName.ORP: "orp",
    MetricName.CHLORINE: "chlorine",
    MetricName.ALKALINITY: "alkalinity",
    MetricName.CYA: "cya",
    MetricName.HARDNESS: "hardness",
    MetricName.SALT: "salt",
    MetricName.TDS: "tds",
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def generate_recommendations(problems: list[Problem]) -> list[Recommendation]:
    """Derive :class:`~.recommendation.Recommendation` objects from detected problems.

    For each :class:`~.problem.Problem`, looks up the matching recommendation
    template in the internal mapping and produces a
    :class:`~.recommendation.Recommendation` with:

    - A :class:`~.recommendation.Treatment` step when a product is known.
    - Priority derived from :attr:`~.problem.Problem.severity`.
    - :attr:`~.recommendation.ActionKind` set based on severity
      (``CRITICAL`` and ``MEDIUM`` → ``REQUIREMENT``, ``LOW`` →
      ``SUGGESTION``).

    Problems with no matching template are silently skipped (forward
    compatibility: new problem codes added before new templates exist will
    not crash the pipeline).

    Duplicate recommendations for the same problem code are deduplicated;
    only the highest-severity one is kept.

    Args:
        problems: List of :class:`~.problem.Problem` objects produced by
            :func:`~.problem.detect_problems`.

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
        template = _PROBLEM_RECOMMENDATIONS.get(code)
        if template is None:
            continue

        rec_type, title, desc_template, product_id, unit = template
        priority = _SEVERITY_TO_PRIORITY[problem.severity]
        kind = _SEVERITY_TO_KIND[problem.severity]

        # Fill description placeholders
        description = desc_template.format(
            value=problem.value if problem.value is not None else "N/A",
        )

        # Build treatment list when a product is known
        treatments: list[Treatment] = []
        if product_id is not None and unit is not None:
            treatments.append(
                Treatment(
                    id=f"{code}_{product_id}",
                    product_id=product_id,
                    name=product_id.replace("_", " ").title(),
                    quantity=0.0,  # dosage calculated by chemistry module; not repeated here
                    unit=unit,
                )
            )

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

    # Sort critical-first
    _priority_order = {
        RecommendationPriority.CRITICAL: 0,
        RecommendationPriority.HIGH: 1,
        RecommendationPriority.MEDIUM: 2,
        RecommendationPriority.LOW: 3,
    }
    recommendations.sort(key=lambda r: _priority_order.get(r.priority, 99))
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

    1. Call :func:`~.problem.detect_problems` to produce a list of
       :class:`~.problem.Problem` objects.
    2. Call :func:`generate_recommendations` to derive a list of
       :class:`~.recommendation.Recommendation` objects.
    3. Return an :class:`AnalysisResult` with both lists and the current
       UTC timestamp.

    Args:
        state: The current pool state snapshot produced by the coordinator.
            All sensor readings may be ``None``; the function handles missing
            data gracefully.

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
    problems = detect_problems(state)
    recommendations = generate_recommendations(problems)
    return AnalysisResult(
        problems=problems,
        recommendations=recommendations,
        timestamp=datetime.now(UTC),
    )
