"""Tests for pool chemistry treatment tracking."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.poolman.domain.model import ActiveTreatment, ChemicalProduct
from custom_components.poolman.domain.treatment import (
    TREATMENT_PROFILES,
    TreatmentProfile,
    compute_active_treatments,
    compute_safe_at,
    compute_swimming_safe,
)

# Fixed reference time for deterministic tests
NOW = datetime(2025, 7, 15, 12, 0, 0, tzinfo=UTC)

# Type alias matching compute_active_treatments signature
type TreatmentEntries = list[tuple[ChemicalProduct, datetime, float | None]]


class TestTreatmentProfiles:
    """Tests for treatment profile completeness and validity."""

    def test_all_chemical_products_have_profiles(self) -> None:
        """Every ChemicalProduct must have a corresponding TreatmentProfile."""
        for product in ChemicalProduct:
            assert product in TREATMENT_PROFILES, f"Missing profile for {product}"

    def test_no_extra_profiles(self) -> None:
        """TREATMENT_PROFILES should not contain keys outside ChemicalProduct."""
        for key in TREATMENT_PROFILES:
            assert key in ChemicalProduct, f"Unknown product key in profiles: {key}"

    def test_profile_count_matches_products(self) -> None:
        assert len(TREATMENT_PROFILES) == len(ChemicalProduct)

    def test_all_profiles_are_treatment_profile_instances(self) -> None:
        for product, profile in TREATMENT_PROFILES.items():
            assert isinstance(profile, TreatmentProfile), (
                f"Profile for {product} is not a TreatmentProfile"
            )

    def test_safety_hours_not_exceed_activity_hours_for_shock_products(self) -> None:
        """For shock products, safety_hours should be <= activity_hours."""
        shock_products = [
            ChemicalProduct.CHLORE_CHOC,
            ChemicalProduct.BROMINE_SHOCK,
            ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR,
        ]
        for product in shock_products:
            profile = TREATMENT_PROFILES[product]
            assert profile.safety_hours <= profile.activity_hours, (
                f"{product}: safety_hours ({profile.safety_hours}) > "
                f"activity_hours ({profile.activity_hours})"
            )

    def test_continuous_products_have_zero_wait(self) -> None:
        """Continuous-release products should have 0 activity and 0 safety hours."""
        continuous = [
            ChemicalProduct.GALET_CHLORE,
            ChemicalProduct.BROMINE_TABLET,
            ChemicalProduct.ACTIVE_OXYGEN_TABLET,
            ChemicalProduct.CLARIFIER,
            ChemicalProduct.METAL_SEQUESTRANT,
            ChemicalProduct.WINTERIZING_PRODUCT,
        ]
        for product in continuous:
            profile = TREATMENT_PROFILES[product]
            assert profile.activity_hours == 0, f"{product} activity_hours should be 0"
            assert profile.safety_hours == 0, f"{product} safety_hours should be 0"


class TestComputeActiveTreatments:
    """Tests for compute_active_treatments."""

    def test_empty_entries_returns_empty(self) -> None:
        assert compute_active_treatments([], NOW) == []

    def test_recent_treatment_is_active(self) -> None:
        """A treatment applied 1h ago with 6h activity should be active."""
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, NOW - timedelta(hours=1), 200.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1
        assert result[0].product == ChemicalProduct.PH_MINUS
        assert result[0].quantity_g == 200.0

    def test_expired_treatment_not_returned(self) -> None:
        """A treatment applied 48h ago with 6h activity and 6h safety is expired."""
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, NOW - timedelta(hours=48), 200.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert result == []

    def test_treatment_in_safety_window_still_active(self) -> None:
        """Chlore choc applied 30h ago: activity=48h (still active), safety=24h (expired).

        Should still be returned because activity period hasn't elapsed.
        """
        entries: TreatmentEntries = [
            (ChemicalProduct.CHLORE_CHOC, NOW - timedelta(hours=30), 500.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1
        assert result[0].product == ChemicalProduct.CHLORE_CHOC

    def test_treatment_past_activity_but_in_safety_window(self) -> None:
        """For a product where safety > activity (hypothetically), the treatment
        should still be returned while within the safety window.

        Using PH_MINUS with 6h activity and 6h safety, applied 5h ago: still active.
        """
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, NOW - timedelta(hours=5), None),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1

    def test_zero_hour_product_not_active(self) -> None:
        """Products with 0 activity and 0 safety hours should never be active."""
        entries: TreatmentEntries = [
            (ChemicalProduct.GALET_CHLORE, NOW - timedelta(seconds=1), 100.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert result == []

    def test_zero_hour_product_at_exact_application_time(self) -> None:
        """A 0/0 product applied at exactly NOW is also not active (now >= safe_at)."""
        entries: TreatmentEntries = [
            (ChemicalProduct.GALET_CHLORE, NOW, 100.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert result == []

    def test_multiple_treatments_mixed(self) -> None:
        """Mix of active and expired treatments."""
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, NOW - timedelta(hours=1), 200.0),  # Active (6h)
            (ChemicalProduct.CHLORE_CHOC, NOW - timedelta(hours=50), 500.0),  # Expired (48h)
            (ChemicalProduct.FLOCCULANT, NOW - timedelta(hours=10), None),  # Active (48h)
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 2
        products = {t.product for t in result}
        assert products == {ChemicalProduct.PH_MINUS, ChemicalProduct.FLOCCULANT}

    def test_quantity_g_none_is_preserved(self) -> None:
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_PLUS, NOW - timedelta(hours=1), None),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1
        assert result[0].quantity_g is None

    def test_active_until_computed_correctly(self) -> None:
        applied_at = NOW - timedelta(hours=2)
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, applied_at, 100.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1
        expected_active_until = applied_at + timedelta(hours=6)
        assert result[0].active_until == expected_active_until

    def test_safe_at_computed_correctly(self) -> None:
        applied_at = NOW - timedelta(hours=2)
        entries: TreatmentEntries = [
            (ChemicalProduct.CHLORE_CHOC, applied_at, 500.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1
        expected_safe_at = applied_at + timedelta(hours=24)
        assert result[0].safe_at == expected_safe_at

    def test_boundary_exactly_at_expiry(self) -> None:
        """Treatment applied exactly activity_hours ago is no longer active."""
        applied_at = NOW - timedelta(hours=6)
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, applied_at, 100.0),
        ]
        result = compute_active_treatments(entries, NOW)
        # now == active_until and now == safe_at, so not active
        assert result == []

    def test_boundary_one_second_before_expiry(self) -> None:
        """Treatment one second before expiry is still active."""
        applied_at = NOW - timedelta(hours=6) + timedelta(seconds=1)
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, applied_at, 100.0),
        ]
        result = compute_active_treatments(entries, NOW)
        assert len(result) == 1


class TestComputeSwimmingSafe:
    """Tests for compute_swimming_safe."""

    def test_no_active_treatments_is_safe(self) -> None:
        assert compute_swimming_safe([], NOW) is True

    def test_all_safety_periods_elapsed(self) -> None:
        """Active treatments whose safety period is past should be safe."""
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.PH_MINUS,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW - timedelta(hours=4),
                safe_at=NOW - timedelta(hours=4),
                quantity_g=200.0,
            ),
        ]
        assert compute_swimming_safe(treatments, NOW) is True

    def test_one_treatment_unsafe(self) -> None:
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.CHLORE_CHOC,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW + timedelta(hours=38),
                safe_at=NOW + timedelta(hours=14),
                quantity_g=500.0,
            ),
        ]
        assert compute_swimming_safe(treatments, NOW) is False

    def test_mixed_safe_and_unsafe(self) -> None:
        """If any treatment is still in safety period, pool is unsafe."""
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.PH_MINUS,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW - timedelta(hours=4),
                safe_at=NOW - timedelta(hours=4),
                quantity_g=200.0,
            ),
            ActiveTreatment(
                product=ChemicalProduct.CHLORE_CHOC,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW + timedelta(hours=38),
                safe_at=NOW + timedelta(hours=14),
                quantity_g=500.0,
            ),
        ]
        assert compute_swimming_safe(treatments, NOW) is False

    def test_safe_at_boundary_exactly_now(self) -> None:
        """Treatment whose safe_at equals NOW should be considered safe."""
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.PH_MINUS,
                applied_at=NOW - timedelta(hours=6),
                active_until=NOW,
                safe_at=NOW,
                quantity_g=100.0,
            ),
        ]
        assert compute_swimming_safe(treatments, NOW) is True


class TestComputeSafeAt:
    """Tests for compute_safe_at."""

    def test_no_treatments_returns_none(self) -> None:
        assert compute_safe_at([]) is None

    def test_zero_hour_products_returns_none(self) -> None:
        """Products with 0/0 profiles have safe_at == applied_at, should return None."""
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.GALET_CHLORE,
                applied_at=NOW,
                active_until=NOW,
                safe_at=NOW,
                quantity_g=100.0,
            ),
        ]
        assert compute_safe_at(treatments) is None

    def test_single_treatment_returns_its_safe_at(self) -> None:
        safe_at = NOW + timedelta(hours=14)
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.CHLORE_CHOC,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW + timedelta(hours=38),
                safe_at=safe_at,
                quantity_g=500.0,
            ),
        ]
        assert compute_safe_at(treatments) == safe_at

    def test_multiple_treatments_returns_latest_safe_at(self) -> None:
        earlier_safe = NOW + timedelta(hours=2)
        later_safe = NOW + timedelta(hours=14)
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.PH_MINUS,
                applied_at=NOW - timedelta(hours=4),
                active_until=NOW + timedelta(hours=2),
                safe_at=earlier_safe,
                quantity_g=200.0,
            ),
            ActiveTreatment(
                product=ChemicalProduct.CHLORE_CHOC,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW + timedelta(hours=38),
                safe_at=later_safe,
                quantity_g=500.0,
            ),
        ]
        assert compute_safe_at(treatments) == later_safe

    def test_mix_of_zero_and_nonzero_safety(self) -> None:
        """Only treatments with actual safety periods affect safe_at."""
        safe_at = NOW + timedelta(hours=14)
        treatments = [
            ActiveTreatment(
                product=ChemicalProduct.GALET_CHLORE,
                applied_at=NOW,
                active_until=NOW,
                safe_at=NOW,
                quantity_g=100.0,
            ),
            ActiveTreatment(
                product=ChemicalProduct.CHLORE_CHOC,
                applied_at=NOW - timedelta(hours=10),
                active_until=NOW + timedelta(hours=38),
                safe_at=safe_at,
                quantity_g=500.0,
            ),
        ]
        assert compute_safe_at(treatments) == safe_at


class TestPoolStateIntegration:
    """Integration tests for PoolState treatment-related fields."""

    def test_water_ok_false_when_swimming_unsafe(self) -> None:
        """water_ok should be False when swimming_safe is False."""
        from custom_components.poolman.domain.model import PoolState

        state = PoolState(swimming_safe=False)
        assert state.water_ok is False

    def test_water_ok_true_when_swimming_safe_and_no_critical(self) -> None:
        from custom_components.poolman.domain.model import PoolState

        state = PoolState(swimming_safe=True)
        assert state.water_ok is True

    def test_water_ok_false_with_critical_recommendations(self) -> None:
        from custom_components.poolman.domain.analysis import AnalysisResult
        from custom_components.poolman.domain.model import PoolState
        from custom_components.poolman.domain.problem import Severity
        from custom_components.poolman.domain.recommendation import (
            ActionKind,
            Recommendation,
            RecommendationPriority,
            RecommendationType,
        )

        rec = Recommendation(
            id="rec_ph_too_high",
            type=RecommendationType.CHEMISTRY,
            severity=Severity.CRITICAL,
            priority=RecommendationPriority.CRITICAL,
            kind=ActionKind.REQUIREMENT,
            title="Lower pH",
            description="pH too high",
            reason="ph_too_high",
        )
        state = PoolState(
            swimming_safe=True,
            analysis_result=AnalysisResult(recommendations=[rec]),
        )
        assert state.water_ok is False

    def test_default_pool_state_has_empty_treatments(self) -> None:
        from custom_components.poolman.domain.model import PoolState

        state = PoolState()
        assert state.active_treatments == []
        assert state.swimming_safe is True
        assert state.safe_at is None


class TestEndToEndTreatmentFlow:
    """End-to-end tests simulating treatment application over time."""

    def test_shock_treatment_lifecycle(self) -> None:
        """Simulate applying shock chlorine and checking safety over time."""
        applied_at = NOW
        entries: TreatmentEntries = [
            (ChemicalProduct.CHLORE_CHOC, applied_at, 500.0),
        ]

        # Immediately after: active and unsafe
        active = compute_active_treatments(entries, applied_at)
        assert len(active) == 1
        assert compute_swimming_safe(active, applied_at) is False

        # After 12h: still active and unsafe
        t_12h = applied_at + timedelta(hours=12)
        active = compute_active_treatments(entries, t_12h)
        assert len(active) == 1
        assert compute_swimming_safe(active, t_12h) is False

        # After 24h: still active but now safe to swim
        t_24h = applied_at + timedelta(hours=24)
        active = compute_active_treatments(entries, t_24h)
        assert len(active) == 1
        assert compute_swimming_safe(active, t_24h) is True

        # After 48h: no longer active at all
        t_48h = applied_at + timedelta(hours=48)
        active = compute_active_treatments(entries, t_48h)
        assert active == []

    def test_multiple_staggered_treatments(self) -> None:
        """Two treatments applied at different times."""
        entries: TreatmentEntries = [
            (ChemicalProduct.PH_MINUS, NOW, 200.0),
            (ChemicalProduct.CHLORE_CHOC, NOW + timedelta(hours=2), 500.0),
        ]

        # At NOW + 1h: both active, unsafe due to both safety periods
        t = NOW + timedelta(hours=1)
        active = compute_active_treatments(entries, t)
        assert len(active) == 2
        assert compute_swimming_safe(active, t) is False

        # At NOW + 7h: pH expired (6h), chlore_choc still active (applied +2h, so 5h in)
        t = NOW + timedelta(hours=7)
        active = compute_active_treatments(entries, t)
        assert len(active) == 1
        assert active[0].product == ChemicalProduct.CHLORE_CHOC

        # At NOW + 26h: chlore_choc safe_at = NOW+2+24 = NOW+26h (boundary)
        t = NOW + timedelta(hours=26)
        active = compute_active_treatments(entries, t)
        assert len(active) == 1  # Still active (activity=48h)
        assert compute_swimming_safe(active, t) is True

    @pytest.mark.parametrize("product", list(ChemicalProduct))
    def test_all_products_have_consistent_behavior(self, product: ChemicalProduct) -> None:
        """Every product should be inactive after max(activity, safety) hours."""
        profile = TREATMENT_PROFILES[product]
        max_hours = max(profile.activity_hours, profile.safety_hours)
        applied_at = NOW
        entries: TreatmentEntries = [(product, applied_at, 100.0)]

        # At exactly max_hours later, treatment should no longer be active
        t_expiry = applied_at + timedelta(hours=max_hours)
        active = compute_active_treatments(entries, t_expiry)
        assert active == [], f"{product} should be inactive after {max_hours}h"
