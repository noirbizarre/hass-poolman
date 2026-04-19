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
    ParameterReport,
    PoolReading,
    PoolState,
    Severity,
)
from custom_components.poolman.domain.problems import detect_problems

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_report(
    status: ChemistryStatus,
    value: float,
    minimum: float,
    maximum: float,
    target: float | None = None,
    score: int = 50,
) -> ParameterReport:
    """Return a ParameterReport with the given attributes."""
    return ParameterReport(
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
            ph=_make_report(ChemistryStatus.GOOD, 7.2, PH_MIN, PH_MAX, score=100),
            orp=_make_report(ChemistryStatus.GOOD, 750.0, ORP_MIN_CRITICAL, ORP_MAX, score=100),
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
            ph=_make_report(ChemistryStatus.WARNING, 7.75, PH_MIN, PH_MAX, score=25),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.LOW

    def test_bad_status_with_positive_score_gives_medium_severity(self) -> None:
        """A BAD parameter with score > 0 maps to Severity.MEDIUM."""
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 7.9, PH_MIN, PH_MAX, score=10),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.MEDIUM

    def test_bad_status_with_zero_score_gives_critical_severity(self) -> None:
        """A BAD parameter with score == 0 maps to Severity.CRITICAL."""
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 9.5, PH_MIN, PH_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL


# ---------------------------------------------------------------------------
# Tests for Problem fields
# ---------------------------------------------------------------------------


class TestProblemFields:
    """Each Problem carries the correct field values."""

    def test_metric_matches_parameter_name(self) -> None:
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 9.0, PH_MIN, PH_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].metric == "ph"

    def test_value_matches_reading(self) -> None:
        report = ChemistryReport(
            tac=_make_report(ChemistryStatus.BAD, 50.0, TAC_MIN, TAC_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].value == 50.0

    def test_expected_range_matches_min_max(self) -> None:
        report = ChemistryReport(
            cya=_make_report(ChemistryStatus.BAD, 90.0, CYA_MIN, CYA_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].expected_range == (CYA_MIN, CYA_MAX)

    def test_code_contains_metric_and_direction_too_high(self) -> None:
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].code == "ph_too_high"

    def test_code_contains_metric_and_direction_too_low(self) -> None:
        report = ChemistryReport(
            orp=_make_report(ChemistryStatus.BAD, 600.0, ORP_MIN_CRITICAL, ORP_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        assert problems[0].code == "orp_too_low"

    def test_message_is_human_readable_string(self) -> None:
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        msg = problems[0].message
        assert "pH" in msg
        assert "too high" in msg
        assert "8.5" in msg

    def test_problem_is_frozen_dataclass(self) -> None:
        """Problem instances must be immutable."""
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.BAD, 8.5, PH_MIN, PH_MAX, score=0),
        )
        problems = detect_problems(_state_with_report(report))
        problem = problems[0]
        # frozen=True raises FrozenInstanceError (a subclass of AttributeError)
        with pytest.raises(AttributeError):
            problem.__setattr__("code", "mutated")


# ---------------------------------------------------------------------------
# Tests for ordering / multiple problems
# ---------------------------------------------------------------------------


class TestProblemOrdering:
    """detect_problems sorts results critical-first."""

    def test_critical_before_medium_before_low(self) -> None:
        report = ChemistryReport(
            ph=_make_report(ChemistryStatus.WARNING, 7.75, PH_MIN, PH_MAX, score=25),  # low
            tac=_make_report(ChemistryStatus.BAD, 200.0, TAC_MIN, TAC_MAX, score=5),  # medium
            cya=_make_report(ChemistryStatus.BAD, 100.0, CYA_MIN, CYA_MAX, score=0),  # critical
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
        assert "ph" in metrics
        assert "orp" in metrics
        assert "free_chlorine" in metrics


# ---------------------------------------------------------------------------
# Tests for all individual parameters
# ---------------------------------------------------------------------------


class TestAllParameters:
    """Every ChemistryReport field can generate a Problem."""

    @pytest.mark.parametrize(
        ("metric", "value", "minimum", "maximum"),
        [
            ("ph", 9.0, PH_MIN, PH_MAX),
            ("orp", 600.0, ORP_MIN_CRITICAL, ORP_MAX),
            ("free_chlorine", 0.1, FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
            ("tds", 2000.0, TDS_MIN, TDS_MAX),
            ("salt", 2000.0, SALT_MIN, SALT_MAX),
            ("tac", 50.0, TAC_MIN, TAC_MAX),
            ("cya", 5.0, CYA_MIN, CYA_MAX),
            ("hardness", 50.0, HARDNESS_MIN, HARDNESS_MAX),
        ],
    )
    def test_bad_parameter_generates_problem(
        self, metric: str, value: float, minimum: float, maximum: float
    ) -> None:
        param_report = _make_report(ChemistryStatus.BAD, value, minimum, maximum, score=0)
        report = ChemistryReport(**{metric: param_report})
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].metric == metric
        assert problems[0].value == value
        assert problems[0].expected_range == (minimum, maximum)

    @pytest.mark.parametrize(
        ("metric", "value", "minimum", "maximum"),
        [
            ("ph", 7.75, PH_MIN, PH_MAX),
            ("orp", 730.0, ORP_MIN_CRITICAL, ORP_MAX),
            ("free_chlorine", 2.8, FREE_CHLORINE_MIN, FREE_CHLORINE_MAX),
            ("tds", 1400.0, TDS_MIN, TDS_MAX),
            ("salt", 2750.0, SALT_MIN, SALT_MAX),
            ("tac", 85.0, TAC_MIN, TAC_MAX),
            ("cya", 22.0, CYA_MIN, CYA_MAX),
            ("hardness", 160.0, HARDNESS_MIN, HARDNESS_MAX),
        ],
    )
    def test_warning_parameter_generates_low_severity_problem(
        self, metric: str, value: float, minimum: float, maximum: float
    ) -> None:
        param_report = _make_report(ChemistryStatus.WARNING, value, minimum, maximum, score=25)
        report = ChemistryReport(**{metric: param_report})
        problems = detect_problems(_state_with_report(report))
        assert len(problems) == 1
        assert problems[0].severity == Severity.LOW
