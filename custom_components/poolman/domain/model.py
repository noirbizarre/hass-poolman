"""Domain models for pool management.

Pure Python models with no Home Assistant dependency.

:class:`Severity` and :class:`MetricName` are the canonical definitions
imported from :mod:`.problem`.  All other shared enums live here alongside
their primary model.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .activation import ActivationChecklist
from .problem import (  # noqa: F401 - re-exported for back-compat
    ChemistryStatus,
    MetricName,
    ParameterReport,
    Severity,
)
from .recommendation import (
    ActionKind,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    Treatment,
)


class PoolShape(StrEnum):
    """Pool shape types."""

    RECTANGULAR = "rectangular"
    ROUND = "round"
    FREEFORM = "freeform"


class FiltrationKind(StrEnum):
    """Type of pool filtration system."""

    SAND = "sand"
    CARTRIDGE = "cartridge"
    DIATOMACEOUS_EARTH = "diatomaceous_earth"
    GLASS = "glass"


class TreatmentType(StrEnum):
    """Water treatment method used in the pool."""

    CHLORINE = "chlorine"
    SALT_ELECTROLYSIS = "salt_electrolysis"
    BROMINE = "bromine"
    ACTIVE_OXYGEN = "active_oxygen"


class PoolMode(StrEnum):
    """Operational mode of the pool.

    Lifecycle order: active -> hibernating -> winter_active / winter_passive
    -> activating -> active.
    """

    ACTIVE = "active"
    HIBERNATING = "hibernating"
    WINTER_ACTIVE = "winter_active"
    WINTER_PASSIVE = "winter_passive"
    ACTIVATING = "activating"


class FiltrationDurationMode(StrEnum):
    """Filtration duration control mode.

    Determines how the daily filtration duration is configured and
    whether it is split across multiple periods.

    - ``manual``: single continuous window, user-set duration.
    - ``dynamic``: single continuous window, auto-computed duration.
    - ``split_static``: two windows, both with user-set durations.
    - ``split_dynamic``: two windows, first user-set + second auto-computed
      to reach the daily recommendation.
    """

    MANUAL = "manual"
    DYNAMIC = "dynamic"
    SPLIT_STATIC = "split_static"
    SPLIT_DYNAMIC = "split_dynamic"

    @property
    def is_split(self) -> bool:
        """Return True if this mode uses two filtration periods."""
        return self in (FiltrationDurationMode.SPLIT_STATIC, FiltrationDurationMode.SPLIT_DYNAMIC)


class MeasureParameter(StrEnum):
    """Pool parameters that support manual measurement.

    These correspond to the chemistry and temperature readings that users
    can record manually when no connected sensor is available.
    """

    PH = "ph"
    ORP = "orp"
    FREE_CHLORINE = "free_chlorine"
    EC = "ec"
    TDS = "tds"
    SALT = "salt"
    TAC = "tac"
    CYA = "cya"
    HARDNESS = "hardness"
    TEMPERATURE = "temperature"


class ChemicalProduct(StrEnum):
    """Chemical products for pool treatment."""

    PH_MINUS = "ph_minus"
    PH_PLUS = "ph_plus"
    CHLORE_CHOC = "chlore_choc"
    GALET_CHLORE = "galet_chlore"
    NEUTRALIZER = "neutralizer"
    TAC_PLUS = "tac_plus"
    SALT = "salt"
    BROMINE_TABLET = "bromine_tablet"
    BROMINE_SHOCK = "bromine_shock"
    ACTIVE_OXYGEN_TABLET = "active_oxygen_tablet"
    ACTIVE_OXYGEN_ACTIVATOR = "active_oxygen_activator"
    FLOCCULANT = "flocculant"
    ANTI_ALGAE = "anti_algae"
    STABILIZER = "stabilizer"
    CLARIFIER = "clarifier"
    METAL_SEQUESTRANT = "metal_sequestrant"
    CALCIUM_HARDNESS_INCREASER = "calcium_hardness_increaser"
    WINTERIZING_PRODUCT = "winterizing_product"


# Products that come as tablets and cannot be measured with a spoon
TABLET_PRODUCTS: frozenset[ChemicalProduct] = frozenset(
    {
        ChemicalProduct.GALET_CHLORE,
        ChemicalProduct.BROMINE_TABLET,
        ChemicalProduct.ACTIVE_OXYGEN_TABLET,
    }
)

# Approximate bulk density (g/mL) for each chemical product.
# Used to convert gram-based dosages to volume (mL) for spoon equivalents.
# Sources: typical pool chemical product data sheets.
PRODUCT_DENSITY_G_PER_ML: dict[ChemicalProduct, float] = {
    ChemicalProduct.PH_MINUS: 1.1,  # Sodium bisulfate, dense granules
    ChemicalProduct.PH_PLUS: 0.55,  # Sodium carbonate (soda ash), light powder
    ChemicalProduct.CHLORE_CHOC: 0.9,  # Calcium hypochlorite / dichlor granules
    ChemicalProduct.GALET_CHLORE: 1.0,  # Pressed tablets (not spoon-measured)
    ChemicalProduct.NEUTRALIZER: 1.1,  # Sodium thiosulfate granules
    ChemicalProduct.TAC_PLUS: 0.9,  # Sodium bicarbonate powder
    ChemicalProduct.SALT: 1.2,  # NaCl crystals
    ChemicalProduct.BROMINE_TABLET: 1.0,  # Pressed tablets (not spoon-measured)
    ChemicalProduct.BROMINE_SHOCK: 0.8,  # Bromine granules
    ChemicalProduct.ACTIVE_OXYGEN_TABLET: 1.0,  # Pressed tablets (not spoon-measured)
    ChemicalProduct.ACTIVE_OXYGEN_ACTIVATOR: 1.0,  # Liquid
    ChemicalProduct.FLOCCULANT: 1.0,  # Liquid
    ChemicalProduct.ANTI_ALGAE: 1.0,  # Liquid
    ChemicalProduct.STABILIZER: 0.75,  # Cyanuric acid granules, low density
    ChemicalProduct.CLARIFIER: 1.0,  # Liquid
    ChemicalProduct.METAL_SEQUESTRANT: 1.1,  # Liquid, slightly dense
    ChemicalProduct.CALCIUM_HARDNESS_INCREASER: 0.85,  # CaCl2 flakes/powder
    ChemicalProduct.WINTERIZING_PRODUCT: 1.0,  # Liquid
}


class DosageAdjustment(BaseModel, frozen=True):
    """A chemical dosage adjustment recommendation."""

    product: ChemicalProduct
    quantity_g: float | None = Field(None, ge=0, description="Quantity in grams")


class SanitizerStatus(BaseModel, frozen=True):
    """Sanitizer evaluation result based on ORP reading and treatment type."""

    product: ChemicalProduct
    severity: Severity


class ChemistryReport(BaseModel, frozen=True):
    """Chemistry status report for all available parameters.

    Each field is None when the corresponding sensor reading is unavailable.
    """

    ph: ParameterReport | None = None
    orp: ParameterReport | None = None
    free_chlorine: ParameterReport | None = None
    tds: ParameterReport | None = None
    salt: ParameterReport | None = None
    tac: ParameterReport | None = None
    cya: ParameterReport | None = None
    hardness: ParameterReport | None = None


class SpoonSize(BaseModel, frozen=True):
    """A named measuring spoon with a known volume.

    Spoon sizes are global (not per-product) and are used to express
    dosage recommendations as a number of scoops/spoons alongside the
    native gram-based quantity.

    Attributes:
        name: Human-readable label for the spoon (e.g. "Small", "Large").
        size_ml: Volume of the spoon in milliliters.
    """

    name: str
    size_ml: float = Field(gt=0, description="Volume of the spoon in milliliters")


class Pool(BaseModel):
    """Physical characteristics of a pool."""

    name: str = "Pool"
    volume_m3: float = Field(gt=0, description="Pool volume in cubic meters")
    shape: PoolShape = PoolShape.RECTANGULAR
    treatment: TreatmentType = TreatmentType.CHLORINE
    filtration_kind: FiltrationKind = FiltrationKind.SAND
    pump_flow_m3h: float = Field(gt=0, description="Pump flow rate in m3/h")
    spoon_sizes: list[SpoonSize] = Field(
        default_factory=list,
        description="Configured measuring spoon sizes for dosage display",
    )

    @property
    def turnovers_per_day(self) -> float:
        """Calculate how many full water turnovers per day at 24h operation."""
        return (self.pump_flow_m3h * 24) / self.volume_m3


def compute_spoon_equivalent(
    quantity_g: float,
    product: ChemicalProduct,
    spoon_sizes: list[SpoonSize],
) -> tuple[float, SpoonSize] | None:
    """Convert a gram-based dosage to a spoon count using the best-fit spoon.

    Converts the gram quantity to milliliters using the product's bulk density,
    then selects the spoon size that produces the smallest relative rounding
    error when rounded to the nearest whole number of spoons.

    Args:
        quantity_g: Dosage amount in grams.
        product: The chemical product (used for density lookup).
        spoon_sizes: Available measuring spoon sizes.

    Returns:
        A tuple of ``(spoon_count, spoon)`` where ``spoon_count`` is the
        rounded number of spoons, or ``None`` if no spoon sizes are
        configured, the product is a tablet, the quantity is zero,
        or the density is unknown.
    """
    if not spoon_sizes or product in TABLET_PRODUCTS or quantity_g <= 0:
        return None

    density = PRODUCT_DENSITY_G_PER_ML.get(product)
    if density is None or density <= 0:
        return None

    quantity_ml = quantity_g / density

    best_spoon: SpoonSize | None = None
    best_count: float = 0
    best_error: float = float("inf")

    for spoon in spoon_sizes:
        exact_count = quantity_ml / spoon.size_ml
        rounded_count = max(1, round(exact_count))
        # Relative error: how far the rounded count is from the exact count
        error = abs(rounded_count - exact_count) / exact_count if exact_count > 0 else float("inf")
        if error < best_error:
            best_error = error
            best_count = rounded_count
            best_spoon = spoon

    if best_spoon is None:  # pragma: no cover
        return None

    return (best_count, best_spoon)


def format_spoon_text(spoon_count: float, spoon_name: str) -> str:
    """Format a spoon count and name into a human-readable string.

    Args:
        spoon_count: Number of spoons (typically a whole number).
        spoon_name: Name of the spoon size.

    Returns:
        Formatted string like ``"6 Large spoons"`` or ``"1 Small spoon"``.
    """
    count_int = int(spoon_count)
    unit = "spoon" if count_int == 1 else "spoons"
    return f"{count_int} {spoon_name} {unit}"


def format_treatment_spoon(
    treatment: Treatment,
    spoon_sizes: list[SpoonSize],
) -> str | None:
    """Return a human-readable spoon equivalent string for a treatment, or None.

    Display-only helper: converts the treatment's gram quantity to a spoon
    count using the pool's configured spoon sizes.  Returns ``None`` when
    no spoon equivalent is applicable (tablet product, no spoon sizes, etc.).

    Args:
        treatment: The treatment whose dosage to express in spoons.
        spoon_sizes: Configured measuring spoon sizes from :attr:`Pool.spoon_sizes`.

    Returns:
        A formatted string like ``"6 Large spoons"`` or ``None``.
    """
    try:
        product = ChemicalProduct(treatment.product_id)
    except ValueError:
        return None

    result = compute_spoon_equivalent(treatment.quantity, product, spoon_sizes)
    if result is None:
        return None

    count, spoon = result
    return format_spoon_text(count, spoon.name)


class PoolReading(BaseModel):
    """Current sensor readings from the pool.

    All values are optional since sensors may be unavailable.
    """

    ph: float | None = Field(None, ge=0, le=14, description="pH level")
    orp: float | None = Field(None, description="ORP in millivolts")
    free_chlorine: float | None = Field(None, ge=0, description="Free chlorine in ppm")
    ec: float | None = Field(None, ge=0, description="Electrical conductivity in µS/cm")
    tds: float | None = Field(None, ge=0, description="Total dissolved solids in ppm")
    salt: float | None = Field(None, ge=0, description="Salt level in ppm")
    temp_c: float | None = Field(None, description="Water temperature in Celsius")
    outdoor_temp_c: float | None = Field(None, description="Outdoor/ambient temperature in Celsius")
    tac: float | None = Field(None, ge=0, description="Total alkalinity in ppm")
    cya: float | None = Field(None, ge=0, description="Cyanuric acid (stabilizer) in ppm")
    hardness: float | None = Field(None, ge=0, description="Calcium hardness in ppm")


class ManualMeasure(BaseModel, frozen=True):
    """A manual measurement recorded by the user.

    Attributes:
        parameter: Which pool parameter was measured.
        value: The measured value.
        measured_at: When the measurement was recorded.
    """

    parameter: MeasureParameter
    value: float
    measured_at: datetime


class ActiveTreatment(BaseModel, frozen=True):
    """A chemical treatment that is currently active or within its safety window.

    Attributes:
        product: The chemical product applied.
        applied_at: When the treatment was applied.
        active_until: When the product stops being active.
        safe_at: When swimming becomes safe again.
        quantity_g: Amount of product used in grams, if known.
    """

    product: ChemicalProduct
    applied_at: datetime
    active_until: datetime
    safe_at: datetime
    quantity_g: float | None = Field(None, ge=0)


class PoolState(BaseModel):
    """Computed state of the pool combining readings, analysis, and mode.

    Attributes:
        mode: Current operational mode of the pool.
        pool: Physical pool configuration used by rules for dosage and
            filtration calculations.  ``None`` when not yet built (e.g. in
            tests that do not need rule evaluation).
        reading: Current effective sensor readings (with manual fallbacks
            applied).
        raw_sensor_reading: Raw sensor-only readings before manual fallbacks.
            Used by :class:`~.rules.maintenance.calibration.CalibrationRule`
            to compare sensor vs. manual values.  ``None`` when not running
            in coordinator context.
        analysis_result: Output of the last :func:`~.analysis.analyze_pool`
            run, containing all detected problems and recommendations.
        filtration_hours: Recommended daily filtration duration in hours.
        water_quality_score: Overall water quality score from 0 to 100.
        chemistry_report: Per-parameter chemistry status report.
        active_treatments: Chemical treatments currently within their
            activity or safety window.
        swimming_safe: True when no active treatment safety period is in
            effect and the pool is in ACTIVE mode.
        safe_at: When swimming will become safe, or ``None`` if already safe.
        manual_measures: Latest manual measurements keyed by parameter.
        reading_sources: Which source provided each reading value
            (``"sensor"``, ``"manual"``, or ``"computed"``).
        boost_remaining: Remaining boost filtration hours (0 when no boost).
        activation: Activation checklist when the pool is in ACTIVATING mode.
    """

    mode: PoolMode = PoolMode.ACTIVE
    pool: Pool | None = None
    reading: PoolReading = Field(default_factory=PoolReading)
    raw_sensor_reading: PoolReading | None = None
    analysis_result: Any = Field(default=None)  # AnalysisResult; Any avoids circular import

    @model_validator(mode="after")
    def _default_analysis_result(self) -> PoolState:
        """Initialise analysis_result to an empty AnalysisResult when None."""
        if self.analysis_result is None:
            # Deferred import to break the model.py ↔ analysis.py circular dep.
            from .analysis import AnalysisResult

            object.__setattr__(self, "analysis_result", AnalysisResult())
        return self

    filtration_hours: float | None = None
    water_quality_score: int | None = Field(None, ge=0, le=100)
    chemistry_report: ChemistryReport = Field(default_factory=ChemistryReport)
    active_treatments: list[ActiveTreatment] = Field(default_factory=list)
    swimming_safe: bool = True
    safe_at: datetime | None = None
    manual_measures: dict[MeasureParameter, ManualMeasure] = Field(default_factory=dict)
    reading_sources: dict[str, str] = Field(default_factory=dict)
    boost_remaining: float = Field(0.0, ge=0, description="Remaining boost filtration hours")
    activation: ActivationChecklist | None = None

    @property
    def recommendations(self) -> list[Recommendation]:
        """Return all recommendations from the latest analysis result."""
        return self.analysis_result.recommendations

    @property
    def water_ok(self) -> bool:
        """Return True if water parameters are within acceptable ranges and pool is safe.

        Considers both water chemistry recommendations and active treatment
        safety periods (e.g., recent shock treatment).
        """
        return len(self.critical_recommendations) == 0 and self.swimming_safe

    @property
    def action_required(self) -> bool:
        """Return True if any recommendation exists."""
        return len(self.analysis_result.recommendations) > 0

    @property
    def critical_recommendations(self) -> list[Recommendation]:
        """Return only high/critical priority recommendations."""
        return [
            r
            for r in self.analysis_result.recommendations
            if r.priority in (RecommendationPriority.HIGH, RecommendationPriority.CRITICAL)
        ]

    @property
    def chemistry_actions(self) -> list[Recommendation]:
        """Return recommendations that are not filtration-related."""
        return [
            r
            for r in self.analysis_result.recommendations
            if r.type != RecommendationType.FILTRATION
        ]

    @property
    def suggestions(self) -> list[Recommendation]:
        """Return chemistry actions classified as suggestions."""
        return [r for r in self.chemistry_actions if r.kind == ActionKind.SUGGESTION]

    @property
    def requirements(self) -> list[Recommendation]:
        """Return chemistry actions classified as requirements."""
        return [r for r in self.chemistry_actions if r.kind == ActionKind.REQUIREMENT]


# Chemistry parameter names evaluated for status changes
_CHEMISTRY_PARAMS: tuple[str, ...] = (
    "ph",
    "orp",
    "free_chlorine",
    "tds",
    "salt",
    "tac",
    "cya",
    "hardness",
)


class StatusChange(BaseModel, frozen=True):
    """A detected status transition between two consecutive pool state updates.

    Attributes:
        type: Event type identifier (``water_status_changed`` or
            ``chemistry_status_changed``).
        parameter: Which parameter changed (``water``, ``ph``, ``orp``,
            ``tac``, ``cya``, or ``hardness``).
        previous_status: Status before the change, or None if the parameter
            was previously unavailable.
        status: Status after the change, or None if the parameter became
            unavailable.
    """

    type: str
    parameter: str
    previous_status: str | None
    status: str | None


def compute_status_changes(previous: PoolState, current: PoolState) -> list[StatusChange]:
    """Detect status changes between two consecutive pool states.

    Detects transitions in:
        - Overall ``water_ok`` status (ok / not_ok)
        - Individual chemistry parameter statuses (good / warning / bad)

    Args:
        previous: The previous pool state.
        current: The current pool state.

    Returns:
        List of detected status changes. Empty if nothing changed.
    """
    changes: list[StatusChange] = []

    # Check overall water_ok status
    if previous.water_ok != current.water_ok:
        changes.append(
            StatusChange(
                type="water_status_changed",
                parameter="water",
                previous_status="ok" if previous.water_ok else "not_ok",
                status="ok" if current.water_ok else "not_ok",
            )
        )

    # Check individual chemistry parameter statuses
    for param in _CHEMISTRY_PARAMS:
        prev_report: ParameterReport | None = getattr(previous.chemistry_report, param)
        new_report: ParameterReport | None = getattr(current.chemistry_report, param)

        prev_status = prev_report.status if prev_report else None
        new_status = new_report.status if new_report else None

        if prev_status != new_status:
            changes.append(
                StatusChange(
                    type="chemistry_status_changed",
                    parameter=param,
                    previous_status=prev_status,
                    status=new_status,
                )
            )

    return changes
