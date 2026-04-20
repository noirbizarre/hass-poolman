"""Tests for pool problem data types.

Covers :class:`~custom_components.poolman.domain.problem.Problem`,
:class:`~custom_components.poolman.domain.problem.Severity`, and
:class:`~custom_components.poolman.domain.problem.MetricName`.

Note: ``detect_problems`` has been removed; rule-based tests now live in
``tests/domain/rules/``.
"""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.problem import (
    MetricName,
    Problem,
    Severity,
)


class TestProblemDataclass:
    """Tests for the Problem frozen dataclass."""

    def test_problem_is_frozen_dataclass(self) -> None:
        """Problem instances must be immutable."""
        p = Problem(
            code="ph_too_high",
            message="pH is too high (8.5).",
            severity=Severity.CRITICAL,
            metric=MetricName.PH,
            value=8.5,
            expected_range=(6.8, 7.8),
        )
        with pytest.raises(AttributeError):
            p.__setattr__("code", "mutated")

    def test_problem_fields(self) -> None:
        p = Problem(
            code="ph_too_high",
            message="pH is too high.",
            severity=Severity.MEDIUM,
            metric=MetricName.PH,
            value=8.1,
            expected_range=(6.8, 7.8),
        )
        assert p.code == "ph_too_high"
        assert p.severity == Severity.MEDIUM
        assert p.metric is MetricName.PH
        assert p.value == pytest.approx(8.1)
        assert p.expected_range == (6.8, 7.8)

    def test_problem_optional_fields(self) -> None:
        """metric, value, and expected_range are all optional (None)."""
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


class TestSeverityEnum:
    """Tests for the Severity enum."""

    def test_severity_values(self) -> None:
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.CRITICAL == "critical"

    def test_severity_ordering(self) -> None:
        """Verify ordering constants are sensible (CRITICAL < MEDIUM < LOW)."""
        order = [Severity.CRITICAL, Severity.MEDIUM, Severity.LOW]
        assert order == [Severity.CRITICAL, Severity.MEDIUM, Severity.LOW]


class TestMetricNameEnum:
    """Tests for the MetricName enum."""

    def test_metric_name_values(self) -> None:
        assert MetricName.PH == "ph"
        assert MetricName.ORP == "orp"
        assert MetricName.CHLORINE == "chlorine"
        assert MetricName.ALKALINITY == "alkalinity"
        assert MetricName.CYA == "cya"
        assert MetricName.HARDNESS == "hardness"
        assert MetricName.SALT == "salt"
        assert MetricName.TDS == "tds"
