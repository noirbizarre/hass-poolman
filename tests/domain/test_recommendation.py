"""Tests for domain recommendation types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from custom_components.poolman.domain.problem import MetricName, Severity
from custom_components.poolman.domain.recommendation import (
    ActionKind,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    Treatment,
)


class TestRecommendationType:
    """Tests for RecommendationType StrEnum."""

    def test_values(self) -> None:
        assert RecommendationType.CHEMISTRY == "chemistry"
        assert RecommendationType.FILTRATION == "filtration"
        assert RecommendationType.ALERT == "alert"
        assert RecommendationType.MAINTENANCE == "maintenance"

    def test_construction_from_string(self) -> None:
        assert RecommendationType("chemistry") == RecommendationType.CHEMISTRY
        assert RecommendationType("alert") == RecommendationType.ALERT

    def test_all_members(self) -> None:
        values = {m.value for m in RecommendationType}
        assert values == {"chemistry", "filtration", "alert", "maintenance"}


class TestRecommendationPriority:
    """Tests for RecommendationPriority StrEnum."""

    def test_values(self) -> None:
        assert RecommendationPriority.LOW == "low"
        assert RecommendationPriority.MEDIUM == "medium"
        assert RecommendationPriority.HIGH == "high"
        assert RecommendationPriority.CRITICAL == "critical"

    def test_construction_from_string(self) -> None:
        assert RecommendationPriority("high") == RecommendationPriority.HIGH

    def test_all_members(self) -> None:
        values = {m.value for m in RecommendationPriority}
        assert values == {"low", "medium", "high", "critical"}


class TestActionKind:
    """Tests for ActionKind StrEnum."""

    def test_values(self) -> None:
        assert ActionKind.SUGGESTION == "suggestion"
        assert ActionKind.REQUIREMENT == "requirement"

    def test_construction_from_string(self) -> None:
        assert ActionKind("suggestion") == ActionKind.SUGGESTION
        assert ActionKind("requirement") == ActionKind.REQUIREMENT

    def test_all_members(self) -> None:
        values = {m.value for m in ActionKind}
        assert values == {"suggestion", "requirement"}


class TestTreatment:
    """Tests for Treatment frozen dataclass."""

    def test_creation(self) -> None:
        t = Treatment(
            id="ph_minus_300g",
            product_id="ph_minus",
            name="pH-",
            quantity=300.0,
            unit="g",
        )
        assert t.id == "ph_minus_300g"
        assert t.product_id == "ph_minus"
        assert t.name == "pH-"
        assert t.quantity == 300.0
        assert t.unit == "g"
        assert t.duration is None

    def test_with_duration(self) -> None:
        t = Treatment(
            id="chlorine_shock",
            product_id="chlore_choc",
            name="Chlore Choc",
            quantity=500.0,
            unit="g",
            duration=timedelta(hours=2),
        )
        assert t.duration == timedelta(hours=2)

    def test_frozen(self) -> None:
        """Treatment should be immutable."""
        t = Treatment(id="t1", product_id="ph_minus", name="pH-", quantity=100.0, unit="g")
        with pytest.raises(FrozenInstanceError):
            t.quantity = 200.0  # type: ignore[misc]  # ty: ignore[invalid-assignment]

    def test_equality(self) -> None:
        t1 = Treatment(id="t1", product_id="ph_minus", name="pH-", quantity=100.0, unit="g")
        t2 = Treatment(id="t1", product_id="ph_minus", name="pH-", quantity=100.0, unit="g")
        assert t1 == t2

    def test_inequality(self) -> None:
        t1 = Treatment(id="t1", product_id="ph_minus", name="pH-", quantity=100.0, unit="g")
        t2 = Treatment(id="t1", product_id="ph_minus", name="pH-", quantity=200.0, unit="g")
        assert t1 != t2


class TestRecommendation:
    """Tests for Recommendation frozen dataclass."""

    def _make_rec(
        self,
        *,
        rec_id: str = "lower_ph",
        rec_type: RecommendationType = RecommendationType.CHEMISTRY,
        severity: Severity = Severity.MEDIUM,
        priority: RecommendationPriority = RecommendationPriority.HIGH,
        kind: ActionKind = ActionKind.REQUIREMENT,
        title: str = "Lower pH",
        description: str = "pH is too high (7.9). Add pH- to bring it back.",
        reason: str = "ph_too_high",
        treatments: list[Treatment] | None = None,
        related_metrics: list[MetricName] | None = None,
    ) -> Recommendation:
        return Recommendation(
            id=rec_id,
            type=rec_type,
            severity=severity,
            priority=priority,
            kind=kind,
            title=title,
            description=description,
            reason=reason,
            treatments=treatments or [],
            related_metrics=related_metrics or [],
        )

    def test_creation_minimal(self) -> None:
        rec = self._make_rec()
        assert rec.id == "lower_ph"
        assert rec.type == RecommendationType.CHEMISTRY
        assert rec.severity == Severity.MEDIUM
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.kind == ActionKind.REQUIREMENT
        assert rec.title == "Lower pH"
        assert rec.reason == "ph_too_high"
        assert rec.treatments == []
        assert rec.related_metrics == []

    def test_creation_with_treatments(self) -> None:
        treatment = Treatment(
            id="ph_minus_300g",
            product_id="ph_minus",
            name="pH-",
            quantity=300.0,
            unit="g",
        )
        rec = self._make_rec(treatments=[treatment], related_metrics=[MetricName.PH])
        assert len(rec.treatments) == 1
        assert rec.treatments[0] == treatment
        assert rec.related_metrics == [MetricName.PH]

    def test_frozen(self) -> None:
        """Recommendation should be immutable."""
        rec = self._make_rec()
        with pytest.raises(FrozenInstanceError):
            rec.title = "Other title"  # type: ignore[misc]  # ty: ignore[invalid-assignment]

    def test_equality(self) -> None:
        rec1 = self._make_rec()
        rec2 = self._make_rec()
        assert rec1 == rec2

    def test_inequality_different_id(self) -> None:
        rec1 = self._make_rec(rec_id="lower_ph")
        rec2 = self._make_rec(rec_id="raise_ph")
        assert rec1 != rec2

    def test_severity_propagated(self) -> None:
        for severity in Severity:
            rec = self._make_rec(severity=severity)
            assert rec.severity == severity

    def test_type_is_strenum(self) -> None:
        rec = self._make_rec()
        assert isinstance(rec.type, str)
        assert rec.type == "chemistry"

    def test_priority_is_strenum(self) -> None:
        rec = self._make_rec()
        assert isinstance(rec.priority, str)
        assert rec.priority == "high"


class TestTreatmentToDict:
    """Tests for :meth:`Treatment.to_dict`."""

    def test_full(self) -> None:
        t = Treatment(
            id="chlorine_shock",
            product_id="chlore_choc",
            name="Chlore Choc",
            quantity=500.0,
            unit="g",
            duration=timedelta(hours=2),
        )
        assert t.to_dict() == {
            "id": "chlorine_shock",
            "product_id": "chlore_choc",
            "name": "Chlore Choc",
            "quantity": 500.0,
            "unit": "g",
            "duration": 7200.0,
        }

    def test_no_duration(self) -> None:
        t = Treatment(
            id="ph_minus_300g",
            product_id="ph_minus",
            name="pH-",
            quantity=300.0,
            unit="g",
        )
        data = t.to_dict()
        assert data["duration"] is None
        # Only plain JSON-safe types
        for value in data.values():
            assert value is None or isinstance(value, (str, int, float))


class TestRecommendationToDict:
    """Tests for :meth:`Recommendation.to_dict`."""

    def _make_rec(self, **overrides: object) -> Recommendation:
        defaults: dict[str, object] = {
            "id": "lower_ph",
            "type": RecommendationType.CHEMISTRY,
            "severity": Severity.MEDIUM,
            "priority": RecommendationPriority.HIGH,
            "kind": ActionKind.REQUIREMENT,
            "title": "Lower pH",
            "description": "pH is too high.",
            "reason": "ph_too_high",
            "treatments": [],
            "related_metrics": [],
        }
        defaults.update(overrides)
        return Recommendation(**defaults)  # type: ignore[arg-type]

    def test_full(self) -> None:
        treatment = Treatment(
            id="ph_minus_300g",
            product_id="ph_minus",
            name="pH-",
            quantity=300.0,
            unit="g",
            duration=timedelta(minutes=30),
        )
        rec = self._make_rec(
            treatments=[treatment],
            related_metrics=[MetricName.PH, MetricName.ORP],
        )

        data = rec.to_dict()

        assert data == {
            "id": "lower_ph",
            "type": "chemistry",
            "severity": "medium",
            "priority": "high",
            "kind": "requirement",
            "title": "Lower pH",
            "description": "pH is too high.",
            "reason": "ph_too_high",
            "treatments": [treatment.to_dict()],
            "related_metrics": ["ph", "orp"],
        }

    def test_empty(self) -> None:
        rec = self._make_rec()
        data = rec.to_dict()
        assert data["treatments"] == []
        assert data["related_metrics"] == []

    def test_enums_serialized_as_plain_strings(self) -> None:
        rec = self._make_rec(related_metrics=[MetricName.CHLORINE])
        data = rec.to_dict()
        for key in ("type", "severity", "priority", "kind"):
            value = data[key]
            assert type(value) is str, f"{key} should be plain str, got {type(value)!r}"
        for metric in data["related_metrics"]:
            assert type(metric) is str
