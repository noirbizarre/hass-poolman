"""Pool management rule engine package.

Public API::

    from custom_components.poolman.domain.rules import (
        Rule, RuleResult, RuleEngine, ALL_RULES,
        PhRule, SanitizerRule, FreeChlorineRule, TacRule,
        AlgaeRiskRule, CyaRule, HardnessRule, SaltRule, TdsRule,
        FiltrationRule, CalibrationRule,
    )
"""

from .base import Rule, RuleResult
from .chemistry.algae import AlgaeRiskRule
from .chemistry.alkalinity import TacRule
from .chemistry.chlorine import FreeChlorineRule
from .chemistry.cya import CyaRule
from .chemistry.hardness import HardnessRule
from .chemistry.ph import PhRule
from .chemistry.salt import SaltRule
from .chemistry.sanitizer import SanitizerRule
from .chemistry.tds import TdsRule
from .engine import RuleEngine
from .filtration.filtration import FiltrationRule
from .maintenance.calibration import CalibrationRule
from .registry import ALL_RULES

__all__ = [
    "ALL_RULES",
    "AlgaeRiskRule",
    "CalibrationRule",
    "CyaRule",
    "FiltrationRule",
    "FreeChlorineRule",
    "HardnessRule",
    "PhRule",
    "Rule",
    "RuleEngine",
    "RuleResult",
    "SaltRule",
    "SanitizerRule",
    "TacRule",
    "TdsRule",
]
