"""Tests for the analysis pipeline (analyze_pool, generate_recommendations, AnalysisResult)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC
from unittest.mock import patch

import pytest

from custom_components.poolman.domain.analysis import (
    AnalysisResult,
    analyze_pool,
    generate_recommendations,
)
from custom_components.poolman.domain.model import (
    ChemistryReport,
    DosageAdjustment,
    PoolReading,
    PoolState,
)
from custom_components.poolman.domain.problem import (
    ChemistryStatus,
    MetricName,
    ParameterReport,
    Problem,
    Severity,
)
from custom_components.poolman.domain.recommendation import (
    ActionKind,
    RecommendationPriority,
    RecommendationType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    metric: MetricName,
    value: float,
    minimum: float,
    maximum: float,
    target: float | None = None,
    status: ChemistryStatus = ChemistryStatus.GOOD,
    score: int = 80,
) -> ParameterReport:
    """Return a ParameterReport with the given parameters."""
    return ParameterReport(
        metric=metric,
        status=status,
        value=value,
        target=target if target is not None else (minimum + maximum) / 2,
        minimum=minimum,
        maximum=maximum,
        score=score,
    )


def _make_state(
    *,
    ph: ParameterReport | None = None,
    orp: ParameterReport | None = None,
    tac: ParameterReport | None = None,
) -> PoolState:
    """Return a PoolState with the given chemistry reports (for legacy tests)."""
    return PoolState(
        chemistry_report=ChemistryReport(ph=ph, orp=orp, tac=tac),
    )


def _make_reading_state(
    *,
    ph: float | None = None,
    orp: float | None = None,
    tac: float | None = None,
) -> PoolState:
    """Return a PoolState with PoolReading set (used by rule-engine-based tests)."""
    return PoolState(
        reading=PoolReading(ph=ph, orp=orp, tac=tac),
    )


# ---------------------------------------------------------------------------
# Tests for AnalysisResult
# ---------------------------------------------------------------------------


class TestAnalysisResult:
    """Tests for the AnalysisResult dataclass."""

    def test_defaults(self) -> None:
        result = AnalysisResult()
        assert result.problems == []
        assert result.recommendations == []
        assert result.timestamp is not None

    def test_with_data(self) -> None:
        problem = Problem(
            code="ph_too_high",
            severity=Severity.MEDIUM,
            metric=MetricName.PH,
            value=8.1,
            message="pH is too high (8.1).",
            expected_range=None,
        )
        result = AnalysisResult(problems=[problem])
        assert len(result.problems) == 1
        assert result.problems[0].code == "ph_too_high"

    def test_frozen(self) -> None:
        """AnalysisResult should be immutable."""
        result = AnalysisResult()
        with pytest.raises(FrozenInstanceError):
            result.problems = []  # type: ignore[misc]  # ty: ignore[invalid-assignment]


# ---------------------------------------------------------------------------
# Tests for generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    """Tests for generate_recommendations."""

    def test_empty_problems_returns_empty(self) -> None:
        assert generate_recommendations([]) == []

    def test_known_code_produces_recommendation(self) -> None:
        problem = Problem(
            code="ph_too_high",
            severity=Severity.MEDIUM,
            metric=MetricName.PH,
            value=8.1,
            message="pH is too high.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert len(recs) == 1
        rec = recs[0]
        assert rec.id == "rec_ph_too_high"
        assert rec.type == RecommendationType.CHEMISTRY
        assert rec.reason == "ph_too_high"
        assert rec.severity == Severity.MEDIUM
        assert rec.priority == RecommendationPriority.MEDIUM
        assert rec.kind == ActionKind.REQUIREMENT
        assert MetricName.PH in rec.related_metrics

    def test_unknown_code_is_silently_skipped(self) -> None:
        problem = Problem(
            code="totally_unknown_code",
            severity=Severity.LOW,
            metric=None,
            value=None,
            message="Unknown problem.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert recs == []

    def test_critical_maps_to_critical_priority(self) -> None:
        problem = Problem(
            code="ph_too_high",
            severity=Severity.CRITICAL,
            metric=MetricName.PH,
            value=9.0,
            message="pH is critically high.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert recs[0].priority == RecommendationPriority.CRITICAL
        assert recs[0].kind == ActionKind.REQUIREMENT

    def test_low_maps_to_low_priority_suggestion(self) -> None:
        problem = Problem(
            code="ph_too_high",
            severity=Severity.LOW,
            metric=MetricName.PH,
            value=7.9,
            message="pH is slightly high.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert recs[0].priority == RecommendationPriority.LOW
        assert recs[0].kind == ActionKind.SUGGESTION

    def test_deduplication_keeps_highest_severity(self) -> None:
        """Duplicate problem codes: only the highest-severity one should produce a rec."""
        low = Problem(
            code="ph_too_high",
            severity=Severity.LOW,
            metric=MetricName.PH,
            value=7.9,
            message="low",
            expected_range=None,
        )
        critical = Problem(
            code="ph_too_high",
            severity=Severity.CRITICAL,
            metric=MetricName.PH,
            value=9.0,
            message="crit",
            expected_range=None,
        )
        recs = generate_recommendations([low, critical])
        assert len(recs) == 1
        assert recs[0].severity == Severity.CRITICAL

    def test_sorted_critical_first(self) -> None:
        """Recommendations should be sorted with critical priority first."""
        low_prob = Problem(
            code="ph_too_high",
            severity=Severity.LOW,
            metric=MetricName.PH,
            value=7.9,
            message="low",
            expected_range=None,
        )
        critical_prob = Problem(
            code="alkalinity_too_low",
            severity=Severity.CRITICAL,
            metric=MetricName.ALKALINITY,
            value=40.0,
            message="critical",
            expected_range=None,
        )
        recs = generate_recommendations([low_prob, critical_prob])
        priorities = [r.priority for r in recs]
        assert priorities.index(RecommendationPriority.CRITICAL) < priorities.index(
            RecommendationPriority.LOW
        )

    def test_recommendation_has_treatment_when_product_known(self) -> None:
        problem = Problem(
            code="ph_too_high",
            severity=Severity.MEDIUM,
            metric=MetricName.PH,
            value=8.1,
            message="pH is too high.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert len(recs[0].treatments) == 1
        assert recs[0].treatments[0].product_id == "ph_minus"

    def test_recommendation_no_treatment_when_no_product(self) -> None:
        """Some problems (e.g., orp_too_low) have no specific product."""
        problem = Problem(
            code="orp_too_low",
            severity=Severity.MEDIUM,
            metric=MetricName.ORP,
            value=500.0,
            message="ORP is too low.",
            expected_range=None,
        )
        recs = generate_recommendations([problem])
        assert recs[0].treatments == []

    def test_chlorine_dosage_quantity_populated_from_reading(self) -> None:
        """chlorine_too_low with a reading that returns a dosage quantity populates it."""
        from custom_components.poolman.domain.model import ChemicalProduct

        problem = Problem(
            code="chlorine_too_low",
            severity=Severity.MEDIUM,
            metric=MetricName.CHLORINE,
            value=0.3,
            message="Free chlorine is too low.",
            expected_range=None,
        )
        reading = PoolReading(free_chlorine=0.3)
        fake_dosage = DosageAdjustment(product=ChemicalProduct.CHLORE_CHOC, quantity_g=250.0)
        with patch(
            "custom_components.poolman.domain.analysis.compute_free_chlorine_adjustment",
            return_value=fake_dosage,
        ):
            recs = generate_recommendations([problem], reading=reading)
        assert len(recs) == 1
        assert len(recs[0].treatments) == 1
        assert recs[0].treatments[0].quantity == 250.0


# ---------------------------------------------------------------------------
# Tests for analyze_pool
# ---------------------------------------------------------------------------


class TestAnalyzePool:
    """Tests for analyze_pool (the main pipeline entrypoint)."""

    def test_normal_case_good_water(self) -> None:
        """Good water values should produce no problems and no recommendations."""
        state = _make_reading_state(ph=7.2)
        result = analyze_pool(state)
        assert isinstance(result, AnalysisResult)
        # Good value should not trigger any pH problem
        ph_problems = [p for p in result.problems if p.metric == MetricName.PH]
        assert ph_problems == []

    def test_all_none_sensors_no_crash(self) -> None:
        """analyze_pool must not raise when all sensor values are None."""
        state = PoolState()  # empty state, all readings None
        result = analyze_pool(state)
        assert isinstance(result, AnalysisResult)
        assert result.problems == []
        assert result.recommendations == []

    def test_single_metric_missing_other_params_evaluated(self) -> None:
        """If one sensor is missing, other sensors should still be evaluated."""
        # orp is missing; ph is provided and out of range
        state = _make_reading_state(ph=8.5, orp=None)
        result = analyze_pool(state)
        ph_problems = [p for p in result.problems if p.metric == MetricName.PH]
        orp_problems = [p for p in result.problems if p.metric == MetricName.ORP]
        assert len(ph_problems) >= 1
        assert orp_problems == []

    def test_result_contains_recommendations_for_problems(self) -> None:
        """A detected problem with a known code should produce a recommendation."""
        state = _make_reading_state(ph=8.5)
        result = analyze_pool(state)
        ph_recs = [r for r in result.recommendations if MetricName.PH in r.related_metrics]
        assert len(ph_recs) >= 1

    def test_timestamp_is_utc(self) -> None:
        """The analysis timestamp should be timezone-aware (UTC)."""

        result = analyze_pool(PoolState())
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.tzinfo == UTC

    def test_problems_sorted_critical_first(self) -> None:
        """Problems in the result should be ordered most-severe first."""
        # Use pH well out of range (critical) and TAC slightly out of range
        state = _make_reading_state(ph=9.5, tac=200.0)
        result = analyze_pool(state)
        if len(result.problems) >= 2:
            _order = {Severity.CRITICAL: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
            for i in range(len(result.problems) - 1):
                assert (
                    _order[result.problems[i].severity] <= _order[result.problems[i + 1].severity]
                )
