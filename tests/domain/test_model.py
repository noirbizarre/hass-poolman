"""Tests for pool domain model status change detection."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.poolman.domain.model import (
    PRODUCT_DENSITY_G_PER_ML,
    TABLET_PRODUCTS,
    ActionKind,
    ChemicalProduct,
    ChemistryReport,
    ChemistryStatus,
    ManualMeasure,
    MeasureParameter,
    ParameterReport,
    Pool,
    PoolState,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    SpoonSize,
    StatusChange,
    compute_spoon_equivalent,
    compute_status_changes,
    format_spoon_text,
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
    free_chlorine_status: ChemistryStatus | None = None,
    salt_status: ChemistryStatus | None = None,
    tac_status: ChemistryStatus | None = None,
    cya_status: ChemistryStatus | None = None,
    hardness_status: ChemistryStatus | None = None,
    tds_status: ChemistryStatus | None = None,
    recommendations: list[Recommendation] | None = None,
) -> PoolState:
    """Build a PoolState with the given chemistry statuses."""
    return PoolState(
        chemistry_report=ChemistryReport(
            ph=_make_report(ph_status) if ph_status else None,
            orp=_make_report(orp_status) if orp_status else None,
            free_chlorine=_make_report(free_chlorine_status) if free_chlorine_status else None,
            salt=_make_report(salt_status) if salt_status else None,
            tac=_make_report(tac_status) if tac_status else None,
            cya=_make_report(cya_status) if cya_status else None,
            hardness=_make_report(hardness_status) if hardness_status else None,
            tds=_make_report(tds_status) if tds_status else None,
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

    @pytest.mark.parametrize(
        "param", ["ph", "orp", "free_chlorine", "salt", "tac", "cya", "hardness", "tds"]
    )
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


class TestPoolTurnoversPerDay:
    """Tests for Pool.turnovers_per_day property."""

    def test_turnovers_per_day(self, pool: Pool) -> None:
        """50m3 pool with 10m3/h pump: (10*24)/50 = 4.8 turnovers."""
        assert pool.turnovers_per_day == pytest.approx(4.8)

    def test_turnovers_high_flow(self) -> None:
        """100m3 pool with 25m3/h pump: (25*24)/100 = 6.0 turnovers."""
        pool = Pool(name="Big", volume_m3=100.0, pump_flow_m3h=25.0)
        assert pool.turnovers_per_day == pytest.approx(6.0)


class TestRecommendationStr:
    """Tests for Recommendation.__str__ method."""

    def test_str_with_quantity_and_product(self) -> None:
        """String should include dosage when both quantity and product are present."""
        rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.HIGH,
            message="Add pH-",
            product="ph_minus",
            quantity_g=150.0,
        )
        assert str(rec) == "Add pH- (150g of ph_minus)"

    def test_str_without_quantity(self) -> None:
        """String should just be the message when no quantity."""
        rec = Recommendation(
            type=RecommendationType.FILTRATION,
            priority=RecommendationPriority.LOW,
            message="Run filtration for 8h",
        )
        assert str(rec) == "Run filtration for 8h"

    def test_str_with_zero_quantity(self) -> None:
        """Zero quantity should fall through to plain message."""
        rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.LOW,
            message="Check levels",
            product="ph_minus",
            quantity_g=0.0,
        )
        # 0.0 is falsy, so falls to plain message
        assert str(rec) == "Check levels"


class TestPoolStateActionRequired:
    """Tests for PoolState.action_required property."""

    def test_no_recommendations_not_required(self) -> None:
        state = PoolState()
        assert state.action_required is False

    def test_with_recommendations_required(self) -> None:
        rec = Recommendation(
            type=RecommendationType.FILTRATION,
            priority=RecommendationPriority.LOW,
            message="Run filtration",
        )
        state = PoolState(recommendations=[rec])
        assert state.action_required is True


class TestActionKind:
    """Tests for ActionKind enum and default value."""

    def test_action_kind_values(self) -> None:
        assert ActionKind.SUGGESTION == "suggestion"
        assert ActionKind.REQUIREMENT == "requirement"

    def test_recommendation_default_kind_is_suggestion(self) -> None:
        rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.LOW,
            message="Test",
        )
        assert rec.kind == ActionKind.SUGGESTION

    def test_recommendation_explicit_kind(self) -> None:
        rec = Recommendation(
            type=RecommendationType.CHEMICAL,
            priority=RecommendationPriority.HIGH,
            kind=ActionKind.REQUIREMENT,
            message="Test",
        )
        assert rec.kind == ActionKind.REQUIREMENT


class TestPoolStateChemistryActions:
    """Tests for PoolState.chemistry_actions, suggestions, and requirements."""

    def _make_rec(
        self,
        rtype: RecommendationType = RecommendationType.CHEMICAL,
        kind: ActionKind = ActionKind.SUGGESTION,
        priority: RecommendationPriority = RecommendationPriority.LOW,
        message: str = "test",
    ) -> Recommendation:
        return Recommendation(type=rtype, priority=priority, kind=kind, message=message)

    def test_chemistry_actions_excludes_filtration(self) -> None:
        chem = self._make_rec(rtype=RecommendationType.CHEMICAL)
        filt = self._make_rec(rtype=RecommendationType.FILTRATION)
        alert = self._make_rec(rtype=RecommendationType.ALERT)
        state = PoolState(recommendations=[chem, filt, alert])

        assert len(state.chemistry_actions) == 2
        assert filt not in state.chemistry_actions
        assert chem in state.chemistry_actions
        assert alert in state.chemistry_actions

    def test_chemistry_actions_empty(self) -> None:
        state = PoolState()
        assert state.chemistry_actions == []

    def test_suggestions_filters_by_kind(self) -> None:
        sug = self._make_rec(kind=ActionKind.SUGGESTION)
        req = self._make_rec(kind=ActionKind.REQUIREMENT)
        state = PoolState(recommendations=[sug, req])

        assert len(state.suggestions) == 1
        assert state.suggestions[0] is sug

    def test_requirements_filters_by_kind(self) -> None:
        sug = self._make_rec(kind=ActionKind.SUGGESTION)
        req = self._make_rec(kind=ActionKind.REQUIREMENT)
        state = PoolState(recommendations=[sug, req])

        assert len(state.requirements) == 1
        assert state.requirements[0] is req

    def test_filtration_excluded_from_suggestions_and_requirements(self) -> None:
        filt = self._make_rec(rtype=RecommendationType.FILTRATION, kind=ActionKind.SUGGESTION)
        state = PoolState(recommendations=[filt])

        assert state.suggestions == []
        assert state.requirements == []
        assert state.chemistry_actions == []

    def test_mixed_recommendations(self) -> None:
        chem_sug = self._make_rec(
            rtype=RecommendationType.CHEMICAL, kind=ActionKind.SUGGESTION, message="chem_sug"
        )
        chem_req = self._make_rec(
            rtype=RecommendationType.CHEMICAL, kind=ActionKind.REQUIREMENT, message="chem_req"
        )
        alert_req = self._make_rec(
            rtype=RecommendationType.ALERT, kind=ActionKind.REQUIREMENT, message="alert_req"
        )
        filt = self._make_rec(
            rtype=RecommendationType.FILTRATION, kind=ActionKind.SUGGESTION, message="filt"
        )
        state = PoolState(recommendations=[chem_sug, chem_req, alert_req, filt])

        assert len(state.chemistry_actions) == 3
        assert len(state.suggestions) == 1
        assert len(state.requirements) == 2


class TestMeasureParameter:
    """Tests for MeasureParameter enum."""

    def test_all_parameters_defined(self) -> None:
        """All expected parameters should be present."""
        expected = {
            "ph",
            "orp",
            "free_chlorine",
            "ec",
            "tds",
            "salt",
            "tac",
            "cya",
            "hardness",
            "temperature",
        }
        assert {p.value for p in MeasureParameter} == expected

    def test_str_values(self) -> None:
        """StrEnum values should work as plain strings."""
        assert MeasureParameter.PH == "ph"
        assert MeasureParameter.ORP == "orp"
        assert MeasureParameter.FREE_CHLORINE == "free_chlorine"
        assert MeasureParameter.EC == "ec"
        assert MeasureParameter.TDS == "tds"
        assert MeasureParameter.SALT == "salt"
        assert MeasureParameter.TAC == "tac"
        assert MeasureParameter.CYA == "cya"
        assert MeasureParameter.HARDNESS == "hardness"
        assert MeasureParameter.TEMPERATURE == "temperature"

    def test_construction_from_string(self) -> None:
        """Should be constructable from string values."""
        assert MeasureParameter("ph") == MeasureParameter.PH
        assert MeasureParameter("temperature") == MeasureParameter.TEMPERATURE


class TestManualMeasure:
    """Tests for ManualMeasure model."""

    def test_creation(self) -> None:
        """ManualMeasure should be created with valid values."""
        ts = datetime(2025, 7, 15, 10, 0, tzinfo=UTC)
        measure = ManualMeasure(
            parameter=MeasureParameter.PH,
            value=7.2,
            measured_at=ts,
        )
        assert measure.parameter == MeasureParameter.PH
        assert measure.value == 7.2
        assert measure.measured_at == ts

    def test_frozen(self) -> None:
        """ManualMeasure should be immutable (frozen)."""
        from pydantic import ValidationError

        ts = datetime(2025, 7, 15, 10, 0, tzinfo=UTC)
        measure = ManualMeasure(
            parameter=MeasureParameter.ORP,
            value=750.0,
            measured_at=ts,
        )
        with pytest.raises(ValidationError):
            measure.value = 800.0  # type: ignore[misc]  # ty: ignore[invalid-assignment]

    def test_equality(self) -> None:
        """Two ManualMeasures with same values should be equal."""
        ts = datetime(2025, 7, 15, 10, 0, tzinfo=UTC)
        m1 = ManualMeasure(parameter=MeasureParameter.PH, value=7.2, measured_at=ts)
        m2 = ManualMeasure(parameter=MeasureParameter.PH, value=7.2, measured_at=ts)
        assert m1 == m2


class TestPoolStateManualMeasures:
    """Tests for PoolState manual_measures and reading_sources fields."""

    def test_default_empty(self) -> None:
        """Default PoolState should have empty manual_measures and reading_sources."""
        state = PoolState()
        assert state.manual_measures == {}
        assert state.reading_sources == {}

    def test_with_manual_measures(self) -> None:
        """PoolState should store manual measures."""
        ts = datetime(2025, 7, 15, 10, 0, tzinfo=UTC)
        measures = {
            MeasureParameter.PH: ManualMeasure(
                parameter=MeasureParameter.PH, value=7.2, measured_at=ts
            ),
        }
        state = PoolState(manual_measures=measures)
        assert MeasureParameter.PH in state.manual_measures
        assert state.manual_measures[MeasureParameter.PH].value == 7.2

    def test_with_reading_sources(self) -> None:
        """PoolState should store reading sources."""
        state = PoolState(reading_sources={"ph": "sensor", "orp": "manual"})
        assert state.reading_sources["ph"] == "sensor"
        assert state.reading_sources["orp"] == "manual"


class TestSpoonSize:
    """Tests for SpoonSize model."""

    def test_creation(self) -> None:
        spoon = SpoonSize(name="Small", size_ml=20.0)
        assert spoon.name == "Small"
        assert spoon.size_ml == 20.0

    def test_frozen(self) -> None:
        from pydantic import ValidationError

        spoon = SpoonSize(name="Small", size_ml=20.0)
        with pytest.raises(ValidationError):
            spoon.name = "Large"  # type: ignore[misc]  # ty: ignore[invalid-assignment]

    def test_size_must_be_positive(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SpoonSize(name="Bad", size_ml=0)
        with pytest.raises(ValidationError):
            SpoonSize(name="Bad", size_ml=-5)

    def test_equality(self) -> None:
        s1 = SpoonSize(name="Small", size_ml=20.0)
        s2 = SpoonSize(name="Small", size_ml=20.0)
        assert s1 == s2


class TestPoolSpoonSizes:
    """Tests for Pool.spoon_sizes field."""

    def test_default_empty(self) -> None:
        pool = Pool(name="Test", volume_m3=50, pump_flow_m3h=10)
        assert pool.spoon_sizes == []

    def test_with_spoon_sizes(self) -> None:
        spoons = [
            SpoonSize(name="Small", size_ml=20),
            SpoonSize(name="Large", size_ml=50),
        ]
        pool = Pool(name="Test", volume_m3=50, pump_flow_m3h=10, spoon_sizes=spoons)
        assert len(pool.spoon_sizes) == 2
        assert pool.spoon_sizes[0].name == "Small"
        assert pool.spoon_sizes[1].name == "Large"


class TestProductDensityTable:
    """Tests for the product density table."""

    def test_all_products_have_density(self) -> None:
        """Every ChemicalProduct should have a density entry."""
        for product in ChemicalProduct:
            assert product in PRODUCT_DENSITY_G_PER_ML, f"Missing density for {product}"

    def test_all_densities_positive(self) -> None:
        for product, density in PRODUCT_DENSITY_G_PER_ML.items():
            assert density > 0, f"Density for {product} must be positive"


class TestTabletProducts:
    """Tests for TABLET_PRODUCTS constant."""

    def test_expected_tablet_products(self) -> None:
        assert ChemicalProduct.GALET_CHLORE in TABLET_PRODUCTS
        assert ChemicalProduct.BROMINE_TABLET in TABLET_PRODUCTS
        assert ChemicalProduct.ACTIVE_OXYGEN_TABLET in TABLET_PRODUCTS

    def test_non_tablet_products_excluded(self) -> None:
        assert ChemicalProduct.PH_MINUS not in TABLET_PRODUCTS
        assert ChemicalProduct.CHLORE_CHOC not in TABLET_PRODUCTS
        assert ChemicalProduct.STABILIZER not in TABLET_PRODUCTS


class TestComputeSpoonEquivalent:
    """Tests for compute_spoon_equivalent."""

    @pytest.fixture
    def small_spoon(self) -> SpoonSize:
        return SpoonSize(name="Small", size_ml=20.0)

    @pytest.fixture
    def large_spoon(self) -> SpoonSize:
        return SpoonSize(name="Large", size_ml=50.0)

    def test_no_spoon_sizes_returns_none(self) -> None:
        result = compute_spoon_equivalent(300.0, ChemicalProduct.PH_MINUS, [])
        assert result is None

    def test_tablet_product_returns_none(self, small_spoon: SpoonSize) -> None:
        result = compute_spoon_equivalent(300.0, ChemicalProduct.GALET_CHLORE, [small_spoon])
        assert result is None

    def test_zero_quantity_returns_none(self, small_spoon: SpoonSize) -> None:
        result = compute_spoon_equivalent(0.0, ChemicalProduct.PH_MINUS, [small_spoon])
        assert result is None

    def test_negative_quantity_returns_none(self, small_spoon: SpoonSize) -> None:
        result = compute_spoon_equivalent(-10.0, ChemicalProduct.PH_MINUS, [small_spoon])
        assert result is None

    def test_single_spoon_exact_fit(self, small_spoon: SpoonSize) -> None:
        """pH- density is 1.1 g/mL. 220g = 200 mL = 10 small spoons (20mL each)."""
        result = compute_spoon_equivalent(220.0, ChemicalProduct.PH_MINUS, [small_spoon])
        assert result is not None
        count, spoon = result
        assert count == 10
        assert spoon.name == "Small"

    def test_single_spoon_rounded(self, large_spoon: SpoonSize) -> None:
        """pH- density is 1.1 g/mL. 300g = 272.7 mL. 272.7/50 = 5.45 -> rounds to 5."""
        result = compute_spoon_equivalent(300.0, ChemicalProduct.PH_MINUS, [large_spoon])
        assert result is not None
        count, spoon = result
        assert count == 5
        assert spoon.name == "Large"

    def test_best_fit_picks_least_error(
        self, small_spoon: SpoonSize, large_spoon: SpoonSize
    ) -> None:
        """Should pick the spoon that minimizes rounding error."""
        # pH+ density is 0.55 g/mL. 55g ≈ 100 mL.
        # Small (20mL): 100/20 = 5.0 -> near-exact fit
        # Large (50mL): 100/50 = 2.0 -> near-exact fit
        # Both are essentially exact; either is a valid result.
        result = compute_spoon_equivalent(55.0, ChemicalProduct.PH_PLUS, [small_spoon, large_spoon])
        assert result is not None
        count, spoon = result
        # Both spoons produce near-exact fits; verify a valid spoon was chosen
        assert (count == 5 and spoon.name == "Small") or (count == 2 and spoon.name == "Large")

    def test_best_fit_prefers_closer_match(self) -> None:
        """Should pick the spoon that gives the closer rounded count."""
        small = SpoonSize(name="Small", size_ml=15.0)
        large = SpoonSize(name="Large", size_ml=40.0)
        # TAC+ density is 0.9 g/mL. 180g = 200 mL.
        # Small (15mL): 200/15 = 13.33 -> rounds to 13, error = 0.33/13.33 = 0.025
        # Large (40mL): 200/40 = 5.0 -> rounds to 5, error = 0
        result = compute_spoon_equivalent(180.0, ChemicalProduct.TAC_PLUS, [small, large])
        assert result is not None
        count, spoon = result
        assert count == 5
        assert spoon.name == "Large"

    def test_minimum_one_spoon(self, large_spoon: SpoonSize) -> None:
        """Very small quantities should still return at least 1 spoon."""
        # pH- density 1.1 g/mL. 1g = 0.91 mL. 0.91/50 = 0.018 -> rounds to 0, clamped to 1
        result = compute_spoon_equivalent(1.0, ChemicalProduct.PH_MINUS, [large_spoon])
        assert result is not None
        count, _ = result
        assert count >= 1

    def test_low_density_product(self, small_spoon: SpoonSize) -> None:
        """pH+ has low density (0.55 g/mL), so same grams = more volume."""
        # 110g pH+ = 200 mL = 10 small spoons
        result = compute_spoon_equivalent(110.0, ChemicalProduct.PH_PLUS, [small_spoon])
        assert result is not None
        count, spoon = result
        assert count == 10
        assert spoon.name == "Small"

    def test_all_tablet_products_return_none(self, small_spoon: SpoonSize) -> None:
        """All tablet products should return None."""
        for product in TABLET_PRODUCTS:
            result = compute_spoon_equivalent(100.0, product, [small_spoon])
            assert result is None, f"Expected None for tablet product {product}"


class TestFormatSpoonText:
    """Tests for format_spoon_text."""

    def test_singular(self) -> None:
        assert format_spoon_text(1, "Large") == "1 Large spoon"

    def test_plural(self) -> None:
        assert format_spoon_text(5, "Small") == "5 Small spoons"

    def test_zero_spoons(self) -> None:
        # Edge case: 0 spoons should say "spoons" (plural)
        assert format_spoon_text(0, "Small") == "0 Small spoons"

    def test_float_count_truncated(self) -> None:
        # Float is truncated to int for display
        assert format_spoon_text(3.7, "Medium") == "3 Medium spoons"
