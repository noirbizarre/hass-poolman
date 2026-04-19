"""Tests for Problem detection in pool chemistry."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.chemistry import (
    CYA_MAX,
    CYA_MIN,
    FREE_CHLORINE_MAX,
    FREE_CHLORINE_MIN,
    HARDNESS_MAX,
    HARDNESS_MIN,
    ORP_MAX,
    ORP_MIN_CRITICAL,
    PH_MAX,
    PH_MIN,
    SALT_MAX,
    SALT_MIN,
    TAC_MAX,
    TAC_MIN,
    TDS_MAX,
    TDS_MIN,
    compute_chemistry_report,
)
from custom_components.poolman.domain.model import (
    ChemistryReport,
    ChemistryStatus,
    MetricName,
    ParameterReport,
    PoolReading,
    PoolState,
    Severity,
)
from custom_components.poolman.domain.problems import Problem, detect_problems

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_report(
    status: ChemistryStatus,
    value: float,
    minimum: float,
    maximum: float,
    metric: MetricName = MetricName.PH,
    target: float | None = None,
    score: int = 50,
) -> ParameterReport:
    """Return a ParameterReport with the given attributes."""
    return ParameterReport(
        metric=metric,
        status=status,
        value=value,
        target=target if target is not None else (minimum + maximum) / 2,
        minimum=minimum,
        maximum=maximum,
        score=score,
    )


def _state_with_report(report: ChemistryReport) -> PoolState:
    """Wrap a ChemistryReport in a minimal PoolState."""
    return PoolState(chemistry_report=report)


# ---------------------------------------------------------------------------
# Tests for detect_problems — nominal (all good)
# ---------------------------------------------------------------------------


class TestDetectProblemsNominal:
    """detect_problems returns empty list when chemistry is fine."""

    def test_good_reading_yields_no_problems(self, good_reading: PoolReading) -> None:
        """All parameters in range → no problems."""
        state = PoolState(chemistry_report=compute_chemistry_report(good_reading))
        assert detect_problems(state) == []

    def test_empty_reading_yields_no_problems(self, empty_reading: PoolReading) -> None:
        """No sensor data → no problems."""
        state = PoolState(chemistry_report=compute_chemistry_report(empty_reading))
        assert detect_problems(state) == []

    def test_no_chemistry_report_yields_no_problems(self) -> None:
        """PoolState without a chemistry_report → no problems."""
        state = PoolState()
        assert detect_problems(state) == []

    def test_all_good_statuses_yield_no_problems(self) -> None:
        """Explicit GOOD status on every parameter → empty list."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.GOOD, 7.2, PH_MIN, PH_MAX, metric=MetricName.PH, score=100
            ),
            orp=_make_report(
                ChemistryStatus.GOOD,
                750.0,
                ORP_MIN_CRITICAL,
                ORP_MAX,
                metric=MetricName.ORP,
                score=100,
            ),
        )
        assert detect_problems(_state_with_report(report)) == []


# ---------------------------------------------------------------------------
# Tests for Problem severity mapping
# ---------------------------------------------------------------------------


class TestProblemSeverity:
    """Severity is mapped correctly from ChemistryStatus + score."""

    def test_warning_status_gives_low_severity(self) -> None:
        """A WARNING parameter maps to Severity.LOW."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.WARNING, 7.75, PH_MIN, PH_MAX, metric=MetricName.PH, score=25
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.LOW

    def test_bad_status_with_positive_score_gives_medium_severity(self) -> None:
        """A BAD parameter with score > 0 maps to Severity.MEDIUM."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 7.9, PH_MIN, PH_MAX, metric=MetricName.PH, score=10
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.MEDIUM

    def test_bad_status_with_zero_score_gives_critical_severity(self) -> None:
        """A BAD parameter with score == 0 maps to Severity.CRITICAL."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 9.5, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL


# ---------------------------------------------------------------------------
# Tests for Problem fields
# ---------------------------------------------------------------------------


class TestProblemFields:
    """Each Problem carries the correct field values."""

    def test_metric_is_metric_name_enum(self) -> None:
        """metric field uses MetricName enum, not a raw string."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 9.0, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].metric is MetricName.PH
        assert isinstance(problems[0].metric, MetricName)

    def test_free_chlorine_maps_to_chlorine_metric(self) -> None:
        """ChemistryReport 'free_chlorine' field maps to MetricName.CHLORINE."""
        report = ChemistryReport(
            free_chlorine=_make_report(
                ChemistryStatus.BAD,
                0.1,
                FREE_CHLORINE_MIN,
                FREE_CHLORINE_MAX,
                metric=MetricName.CHLORINE,
                score=0,
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].metric is MetricName.CHLORINE

    def test_tac_maps_to_alkalinity_metric(self) -> None:
        """ChemistryReport 'tac' field maps to MetricName.ALKALINITY."""
        report = ChemistryReport(
            tac=_make_report(
                ChemistryStatus.BAD, 50.0, TAC_MIN, TAC_MAX, metric=MetricName.ALKALINITY, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].metric is MetricName.ALKALINITY

    def test_value_matches_reading(self) -> None:
        report = ChemistryReport(
            tac=_make_report(
                ChemistryStatus.BAD, 50.0, TAC_MIN, TAC_MAX, metric=MetricName.ALKALINITY, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].value == 50.0

    def test_expected_range_matches_min_max(self) -> None:
        report = ChemistryReport(
            cya=_make_report(
                ChemistryStatus.BAD, 90.0, CYA_MIN, CYA_MAX, metric=MetricName.CYA, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].expected_range == (CYA_MIN, CYA_MAX)

    def test_code_contains_field_and_direction_too_high(self) -> None:
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].code == "ph_too_high"

    def test_code_contains_field_and_direction_too_low(self) -> None:
        report = ChemistryReport(
            orp=_make_report(
                ChemistryStatus.BAD,
                600.0,
                ORP_MIN_CRITICAL,
                ORP_MAX,
                metric=MetricName.ORP,
                score=0,
            ),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].code == "orp_too_low"

    def test_message_is_human_readable_string(self) -> None:
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        msg = problems[0].message
        assert "pH" in msg
        assert "too high" in msg
        assert "8.5" in msg

    def test_problem_is_frozen_dataclass(self) -> None:
        """Problem instances must be immutable."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
        )
        problems = detect_problems(_state_with_report(report))
        problem = problems[0]
        # frozen=True raises FrozenInstanceError (a subclass of AttributeError)
        with pytest.raises(AttributeError):
            problem.__setattr__("code", "mutated")


# ---------------------------------------------------------------------------
# Tests for optional / partial data resilience
# ---------------------------------------------------------------------------


class TestPartialDataResilience:
    """detect_problems gracefully handles missing or partial data."""

    def test_metric_field_is_none_for_unknown_fields(self) -> None:
        """A Problem built from an unmapped field has metric=None."""
        # Simulate a future field that has no MetricName mapping by
        # directly constructing a Problem with metric=None.
        p = Problem(
            code="unknown_out_of_range",
            message="unknown is out of range",
            severity=Severity.LOW,
            metric=None,
            value=None,
            expected_range=None,
        )
        assert p.metric is None
        assert p.value is None
        assert p.expected_range is None

    def test_detect_problems_does_not_crash_on_none_report(self) -> None:
        """PoolState with chemistry_report=None returns empty list without raising."""
        state = PoolState()
        result = detect_problems(state)
        assert result == []

    def test_detect_problems_does_not_crash_on_partial_report(self) -> None:
        """ChemistryReport with some fields None returns only non-None problems."""
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.BAD, 9.0, PH_MIN, PH_MAX, metric=MetricName.PH, score=0
            ),
            orp=None,
            tac=None,
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].metric is MetricName.PH

    def test_detect_problems_is_deterministic(self, bad_reading: PoolReading) -> None:
        """Same PoolState always produces identical problem lists."""
        state = PoolState(chemistry_report=compute_chemistry_report(bad_reading))
        first = detect_problems(state)
        second = detect_problems(state)
        assert first == second


# ---------------------------------------------------------------------------
# Tests for ordering / multiple problems
# ---------------------------------------------------------------------------


class TestProblemOrdering:
    """detect_problems sorts results critical-first."""

    def test_critical_before_medium_before_low(self) -> None:
        report = ChemistryReport(
            ph=_make_report(
                ChemistryStatus.WARNING, 7.75, PH_MIN, PH_MAX, metric=MetricName.PH, score=25
            ),  # low
            tac=_make_report(
                ChemistryStatus.BAD, 200.0, TAC_MIN, TAC_MAX, metric=MetricName.ALKALINITY, score=5
            ),  # medium
            cya=_make_report(
                ChemistryStatus.BAD, 100.0, CYA_MIN, CYA_MAX, metric=MetricName.CYA, score=0
            ),  # critical
        )
        problems = detect_problems(_state_with_report(report))
        severities = [p.severity for p in problems]
        assert severities == [Severity.CRITICAL, Severity.MEDIUM, Severity.LOW]

    def test_bad_reading_generates_multiple_problems(self, bad_reading: PoolReading) -> None:
        """Out-of-range reading produces multiple Problem objects."""
        state = PoolState(chemistry_report=compute_chemistry_report(bad_reading))
        problems = detect_problems(state)
        assert len(problems) > 1
        metrics = {p.metric for p in problems}
        # ph=8.2 (max 7.8), orp=600 (min 650), free_chlorine=0.5 (min 1.0)
        assert MetricName.PH in metrics
        assert MetricName.ORP in metrics
        assert MetricName.CHLORINE in metrics


# ---------------------------------------------------------------------------
# Tests for all individual parameters
# ---------------------------------------------------------------------------


class TestAllParameters:
    """Every ChemistryReport field maps to a MetricName and can generate a Problem."""

    @pytest.mark.parametrize(
        ("field", "metric_name", "value", "minimum", "maximum"),
        [
            ("ph", MetricName.PH, 9.0, PH_MIN, PH_MAX),
            ("orp", MetricName.ORP, 600.0, ORP_MIN_CRITICAL, ORP_MAX),
            ("free_chlorine", MetricName.CHLORINE, 0.1, FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
            ("tds", MetricName.TDS, 2000.0, TDS_MIN, TDS_MAX),
            ("salt", MetricName.SALT, 2000.0, SALT_MIN, SALT_MAX),
            ("tac", MetricName.ALKALINITY, 50.0, TAC_MIN, TAC_MAX),
            ("cya", MetricName.CYA, 5.0, CYA_MIN, CYA_MAX),
            ("hardness", MetricName.HARDNESS, 50.0, HARDNESS_MIN, HARDNESS_MAX),
        ],
    )
    def test_bad_parameter_generates_problem_with_metric_name(
        self,
        field: str,
        metric_name: MetricName,
        value: float,
        minimum: float,
        maximum: float,
    ) -> None:
        param_report = _make_report(
            ChemistryStatus.BAD, value, minimum, maximum, metric=metric_name, score=0
        )
        report = ChemistryReport(**{field: param_report})
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].metric is metric_name
        assert isinstance(problems[0].metric, MetricName)
        assert problems[0].value == value
        assert problems[0].expected_range == (minimum, maximum)

    @pytest.mark.parametrize(
        ("field", "metric_name", "value", "minimum", "maximum"),
        [
            ("ph", MetricName.PH, 7.75, PH_MIN, PH_MAX),
            ("orp", MetricName.ORP, 730.0, ORP_MIN_CRITICAL, ORP_MAX),
            ("free_chlorine", MetricName.CHLORINE, 2.8, FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
            ("tds", MetricName.TDS, 1400.0, TDS_MIN, TDS_MAX),
            ("salt", MetricName.SALT, 2750.0, SALT_MIN, SALT_MAX),
            ("tac", MetricName.ALKALINITY, 85.0, TAC_MIN, TAC_MAX),
            ("cya", MetricName.CYA, 22.0, CYA_MIN, CYA_MAX),
            ("hardness", MetricName.HARDNESS, 160.0, HARDNESS_MIN, HARDNESS_MAX),
        ],
    )
    def test_warning_parameter_generates_low_severity_problem(
        self,
        field: str,
        metric_name: MetricName,
        value: float,
        minimum: float,
        maximum: float,
    ) -> None:
        param_report = _make_report(
            ChemistryStatus.WARNING, value, minimum, maximum, metric=metric_name, score=25
        )
        report = ChemistryReport(**{field: param_report})
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.LOW
        assert problems[0].metric is metric_name
