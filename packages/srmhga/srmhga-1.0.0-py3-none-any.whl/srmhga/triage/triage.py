"""UBTP (Uncertainty-Based Triage Protocol).

UBTP selects between:
- FastSemanticPath (AQSRL)
- DeterministicPath (DV)

Decision rule (simplified):
1) if sensitivity is HIGH -> deterministic
2) else if conf >= alpha and margin >= delta_min -> fast semantic
3) else -> deterministic
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..core.config import Config
from ..core.types import Sensitivity
from .sensitivity import SensitivityDetector


class TriagePath(str, Enum):
    FAST_SEMANTIC = "FAST_SEMANTIC"
    DETERMINISTIC = "DETERMINISTIC"


@dataclass(slots=True)
class TriageDecision:
    path: TriagePath
    sensitivity: Sensitivity
    conf: float
    margin: float


class UBTPGate:
    """Implements the UBTP triage gate."""

    def __init__(self, cfg: Config, detector: SensitivityDetector | None = None) -> None:
        self.cfg = cfg.validate()
        self.detector = detector or SensitivityDetector.default()

    def decide(self, query: str, *, conf: float, margin: float) -> TriageDecision:
        sens = self.detector.detect(query)
        if sens is Sensitivity.HIGH:
            return TriageDecision(TriagePath.DETERMINISTIC, sens, float(conf), float(margin))
        if float(conf) >= self.cfg.alpha and float(margin) >= self.cfg.delta_min:
            return TriageDecision(TriagePath.FAST_SEMANTIC, sens, float(conf), float(margin))
        return TriageDecision(TriagePath.DETERMINISTIC, sens, float(conf), float(margin))
