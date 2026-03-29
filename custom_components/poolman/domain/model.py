"""Domain models for pool management.

Pure Python models with no Home Assistant dependency.
"""

from __future__ import annotations

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
    message: str
    product: str | None = None
    quantity_g: float | None = Field(None, ge=0, description="Quantity in grams")

    def __str__(self) -> str:
        """Return human-readable recommendation."""
        if self.quantity_g and self.product:
            return f"{self.message} ({self.quantity_g:.0f}g of {self.product})"
        return self.message


class PoolState(BaseModel):
    """Computed state of the pool combining readings, mode, and recommendations."""

    mode: PoolMode = PoolMode.RUNNING
    reading: PoolReading = Field(default_factory=PoolReading)
    recommendations: list[Recommendation] = Field(default_factory=list)
    filtration_hours: float | None = None
    water_quality_score: int | None = Field(None, ge=0, le=100)

    @property
    def water_ok(self) -> bool:
        """Return True if water parameters are within acceptable ranges."""
        return len(self.critical_recommendations) == 0

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
