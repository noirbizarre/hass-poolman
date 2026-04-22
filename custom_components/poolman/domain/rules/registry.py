"""Registry of all built-in pool management rules.

``ALL_RULES`` is the canonical ordered list of rule instances used by the
default analysis pipeline.  Pass it directly to :class:`~.engine.RuleEngine`::

    engine = RuleEngine(ALL_RULES)
    problems = engine.evaluate(state)
"""

from __future__ import annotations

from .base import Rule
from .chemistry.algae import AlgaeRiskRule
from .chemistry.alkalinity import TacRule
from .chemistry.chlorine import FreeChlorineRule
from .chemistry.cya import CyaRule
from .chemistry.hardness import HardnessRule
from .chemistry.ph import PhRule
from .chemistry.salt import SaltRule
from .chemistry.sanitizer import SanitizerRule
from .chemistry.tds import TdsRule
from .filtration.filtration import FiltrationRule
from .maintenance.calibration import CalibrationRule

ALL_RULES: list[Rule] = [
    PhRule(),
    SanitizerRule(),
    FreeChlorineRule(),
    FiltrationRule(),
    TacRule(),
    AlgaeRiskRule(),
    CyaRule(),
    HardnessRule(),
    SaltRule(),
    TdsRule(),
    CalibrationRule(),
]
