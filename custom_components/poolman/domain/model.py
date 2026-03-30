"""Domain models for pool management.

Pure Python models with no Home Assistant dependency.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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
    """Operational mode of the pool."""

    RUNNING = "running"
    WINTER_ACTIVE = "winter_active"
    WINTER_PASSIVE = "winter_passive"


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


class ChemistryStatus(StrEnum):
    """Status levels for individual chemistry parameters."""

    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"


class Severity(StrEnum):
    """Severity levels for chemistry status."""

    MEDIUM = "medium"
    CRITICAL = "critical"


class RecommendationType(StrEnum):
    """Types of pool recommendations."""

    CHEMICAL = "chemical"
    FILTRATION = "filtration"
    ALERT = "alert"
    MAINTENANCE = "maintenance"


class ActionKind(StrEnum):
    """Whether a recommendation is a suggestion or a requirement.

    Suggestions are optional improvements; requirements indicate
    that the pool needs attention to remain safe or functional.
    """

    SUGGESTION = "suggestion"
    REQUIREMENT = "requirement"


class RecommendationPriority(StrEnum):
    """Priority levels for recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DosageAdjustment(BaseModel, frozen=True):
    """A chemical dosage adjustment recommendation."""

    product: ChemicalProduct
    quantity_g: float | None = Field(None, ge=0, description="Quantity in grams")


class SanitizerStatus(BaseModel, frozen=True):
    """Sanitizer evaluation result based on ORP reading and treatment type."""

    product: ChemicalProduct
    severity: Severity


class ParameterReport(BaseModel, frozen=True):
    """Status report for a single chemistry parameter.

    Bundles the evaluated status with the reading value, target range,
    and individual quality score for rich dashboard display.
    """

    status: ChemistryStatus
    value: float
    target: float
    minimum: float
    maximum: float
    score: int = Field(ge=0, le=100, description="Quality score from 0 to 100")


class ChemistryReport(BaseModel, frozen=True):
    """Chemistry status report for all available parameters.

    Each field is None when the corresponding sensor reading is unavailable.
    """

    ph: ParameterReport | None = None
    orp: ParameterReport | None = None
    tac: ParameterReport | None = None
    cya: ParameterReport | None = None
    hardness: ParameterReport | None = None


class Pool(BaseModel):
    """Physical characteristics of a pool."""

    name: str = "Pool"
    volume_m3: float = Field(gt=0, description="Pool volume in cubic meters")
    shape: PoolShape = PoolShape.RECTANGULAR
    treatment: TreatmentType = TreatmentType.CHLORINE
    filtration_kind: FiltrationKind = FiltrationKind.SAND
    pump_flow_m3h: float = Field(gt=0, description="Pump flow rate in m3/h")

    @property
    def turnovers_per_day(self) -> float:
        """Calculate how many full water turnovers per day at 24h operation."""
        return (self.pump_flow_m3h * 24) / self.volume_m3


class PoolReading(BaseModel):
    """Current sensor readings from the pool.

    All values are optional since sensors may be unavailable.
    """

    ph: float | None = Field(None, ge=0, le=14, description="pH level")
    orp: float | None = Field(None, description="ORP in millivolts")
    temp_c: float | None = Field(None, description="Water temperature in Celsius")
    outdoor_temp_c: float | None = Field(None, description="Outdoor/ambient temperature in Celsius")
    tac: float | None = Field(None, ge=0, description="Total alkalinity in ppm")
    cya: float | None = Field(None, ge=0, description="Cyanuric acid (stabilizer) in ppm")
    hardness: float | None = Field(None, ge=0, description="Calcium hardness in ppm")


class Recommendation(BaseModel):
    """A pool treatment or maintenance recommendation."""

    type: RecommendationType
    priority: RecommendationPriority
    kind: ActionKind = ActionKind.SUGGESTION
    message: str
    product: str | None = None
    quantity_g: float | None = Field(None, ge=0, description="Quantity in grams")

    def __str__(self) -> str:
        """Return human-readable recommendation."""
        if self.quantity_g and self.product:
            return f"{self.message} ({self.quantity_g:.0f}g of {self.product})"
        return self.message


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
    """Computed state of the pool combining readings, mode, and recommendations."""

    mode: PoolMode = PoolMode.RUNNING
    reading: PoolReading = Field(default_factory=PoolReading)
    recommendations: list[Recommendation] = Field(default_factory=list)
    filtration_hours: float | None = None
    water_quality_score: int | None = Field(None, ge=0, le=100)
    chemistry_report: ChemistryReport = Field(default_factory=ChemistryReport)
    active_treatments: list[ActiveTreatment] = Field(default_factory=list)
    swimming_safe: bool = True
    safe_at: datetime | None = None
    manual_measures: dict[MeasureParameter, ManualMeasure] = Field(default_factory=dict)
    reading_sources: dict[str, str] = Field(default_factory=dict)
    boost_remaining: float = Field(0.0, ge=0, description="Remaining boost filtration hours")

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
        return len(self.recommendations) > 0

    @property
    def critical_recommendations(self) -> list[Recommendation]:
        """Return only high/critical priority recommendations."""
        return [
            r
            for r in self.recommendations
            if r.priority in (RecommendationPriority.HIGH, RecommendationPriority.CRITICAL)
        ]

    @property
    def chemistry_actions(self) -> list[Recommendation]:
        """Return only chemistry-related recommendations (excludes filtration)."""
        return [r for r in self.recommendations if r.type != RecommendationType.FILTRATION]

    @property
    def suggestions(self) -> list[Recommendation]:
        """Return chemistry actions classified as suggestions."""
        return [r for r in self.chemistry_actions if r.kind == ActionKind.SUGGESTION]

    @property
    def requirements(self) -> list[Recommendation]:
        """Return chemistry actions classified as requirements."""
        return [r for r in self.chemistry_actions if r.kind == ActionKind.REQUIREMENT]


# Chemistry parameter names evaluated for status changes
_CHEMISTRY_PARAMS: tuple[str, ...] = ("ph", "orp", "tac", "cya", "hardness")


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
