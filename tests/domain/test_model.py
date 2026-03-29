"""Tests for pool domain model status change detection."""

from __future__ import annotations

import pytest

from custom_components.poolman.domain.model import (
    ChemistryReport,
    ChemistryStatus,
    ParameterReport,
    PoolState,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    StatusChange,
    compute_status_changes,
)


def _make_report(
    status: ChemistryStatus,
    value: float = 7.2,
    target: float = 7.2,
    minimum: float = 6.8,
    maximum: float = 7.8,
    score: int = 100,
) -> ParameterReport:
    """Build a ParameterReport with the given status and sensible defaults."""
    return ParameterReport(
        status=status,
        value=value,
        target=target,
        minimum=minimum,
        maximum=maximum,
        score=score,
    )


def _make_state(
    *,
    ph_status: ChemistryStatus | None = None,
    orp_status: ChemistryStatus | None = None,
    tac_status: ChemistryStatus | None = None,
    cya_status: ChemistryStatus | None = None,
    hardness_status: ChemistryStatus | None = None,
    recommendations: list[Recommendation] | None = None,
) -> PoolState:
    """Build a PoolState with the given chemistry statuses."""
    return PoolState(
        chemistry_report=ChemistryReport(
            ph=_make_report(ph_status) if ph_status else None,
            orp=_make_report(orp_status) if orp_status else None,
            tac=_make_report(tac_status) if tac_status else None,
            cya=_make_report(cya_status) if cya_status else None,
            hardness=_make_report(hardness_status) if hardness_status else None,
        ),
        recommendations=recommendations or [],
    )


class TestComputeStatusChanges:
    """Tests for compute_status_changes."""

    def test_no_changes_returns_empty(self) -> None:
        state = _make_state(ph_status=ChemistryStatus.GOOD)
        assert compute_status_changes(state, state) == []

    def test_identical_states_returns_empty(self) -> None:
        state1 = _make_state(
            ph_status=ChemistryStatus.GOOD,
            orp_status=ChemistryStatus.WARNING,
        )
        state2 = _make_state(
            ph_status=ChemistryStatus.GOOD,
            orp_status=ChemistryStatus.WARNING,
        )
        assert compute_status_changes(state1, state2) == []

    def test_ph_good_to_warning(self) -> None:
        prev = _make_state(ph_status=ChemistryStatus.GOOD)
        curr = _make_state(ph_status=ChemistryStatus.WARNING)
        changes = compute_status_changes(prev, curr)

        assert len(changes) == 1
        assert changes[0] == StatusChange(
            type="chemistry_status_changed",
            parameter="ph",
            previous_status="good",
            status="warning",
        )

    def test_ph_warning_to_bad(self) -> None:
        prev = _make_state(ph_status=ChemistryStatus.WARNING)
        curr = _make_state(ph_status=ChemistryStatus.BAD)
        changes = compute_status_changes(prev, curr)

        assert len(changes) == 1
        assert changes[0].parameter == "ph"
        assert changes[0].previous_status == "warning"
        assert changes[0].status == "bad"

    def test_ph_bad_to_good(self) -> None:
        prev = _make_state(ph_status=ChemistryStatus.BAD)
        curr = _make_state(ph_status=ChemistryStatus.GOOD)
        changes = compute_status_changes(prev, curr)

        assert len(changes) == 1
        assert changes[0].previous_status == "bad"
        assert changes[0].status == "good"

    def test_parameter_becomes_available(self) -> None:
        prev = _make_state()
        curr = _make_state(ph_status=ChemistryStatus.GOOD)
        changes = compute_status_changes(prev, curr)

        assert len(changes) == 1
        assert changes[0].parameter == "ph"
        assert changes[0].previous_status is None
        assert changes[0].status == "good"

    def test_parameter_becomes_unavailable(self) -> None:
        prev = _make_state(ph_status=ChemistryStatus.GOOD)
        curr = _make_state()
        changes = compute_status_changes(prev, curr)

        assert len(changes) == 1
        assert changes[0].parameter == "ph"
        assert changes[0].previous_status == "good"
        assert changes[0].status is None

    def test_multiple_parameters_change(self) -> None:
        prev = _make_state(
            ph_status=ChemistryStatus.GOOD,
            orp_status=ChemistryStatus.GOOD,
            tac_status=ChemistryStatus.WARNING,
        )
        curr = _make_state(
            ph_status=ChemistryStatus.WARNING,
            orp_status=ChemistryStatus.BAD,
            tac_status=ChemistryStatus.WARNING,
        )
        changes = compute_status_changes(prev, curr)

        # pH and ORP changed, TAC unchanged
        assert len(changes) == 2
        params = {c.parameter for c in changes}
        assert params == {"ph", "orp"}

    def test_water_ok_to_not_ok(self) -> None:
        prev = _make_state()  # No recommendations -> water_ok=True
        critical_rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.HIGH,
            message="pH too high",
        )
        curr = _make_state(recommendations=[critical_rec])
        changes = compute_status_changes(prev, curr)

        water_changes = [c for c in changes if c.type == "water_status_changed"]
        assert len(water_changes) == 1
        assert water_changes[0].parameter == "water"
        assert water_changes[0].previous_status == "ok"
        assert water_changes[0].status == "not_ok"

    def test_water_not_ok_to_ok(self) -> None:
        critical_rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.HIGH,
            message="pH too high",
        )
        prev = _make_state(recommendations=[critical_rec])
        curr = _make_state()
        changes = compute_status_changes(prev, curr)

        water_changes = [c for c in changes if c.type == "water_status_changed"]
        assert len(water_changes) == 1
        assert water_changes[0].previous_status == "not_ok"
        assert water_changes[0].status == "ok"

    def test_water_ok_unchanged_no_event(self) -> None:
        state = _make_state()  # water_ok=True
        changes = compute_status_changes(state, state)
        water_changes = [c for c in changes if c.type == "water_status_changed"]
        assert water_changes == []

    def test_water_and_chemistry_change_together(self) -> None:
        critical_rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.HIGH,
            message="pH too high",
        )
        prev = _make_state(ph_status=ChemistryStatus.GOOD)
        curr = _make_state(
            ph_status=ChemistryStatus.BAD,
            recommendations=[critical_rec],
        )
        changes = compute_status_changes(prev, curr)

        types = {c.type for c in changes}
        assert types == {"water_status_changed", "chemistry_status_changed"}

    @pytest.mark.parametrize("param", ["ph", "orp", "tac", "cya", "hardness"])
    def test_all_chemistry_params_detected(self, param: str) -> None:
        good_report = _make_report(ChemistryStatus.GOOD)
        bad_report = _make_report(ChemistryStatus.BAD)
        prev = PoolState(
            chemistry_report=ChemistryReport(**{param: good_report}),
        )
        curr = PoolState(
            chemistry_report=ChemistryReport(**{param: bad_report}),
        )
        changes = compute_status_changes(prev, curr)

        chem_changes = [c for c in changes if c.type == "chemistry_status_changed"]
        assert len(chem_changes) == 1
        assert chem_changes[0].parameter == param

    def test_both_none_no_change(self) -> None:
        prev = _make_state()  # All chemistry params None
        curr = _make_state()
        changes = compute_status_changes(prev, curr)

        chem_changes = [c for c in changes if c.type == "chemistry_status_changed"]
        assert chem_changes == []
