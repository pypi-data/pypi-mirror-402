"""Sensitivity detection.

The initial implementation is regex-based. It is intentionally conservative:
false positives are acceptable because they route to the deterministic path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Pattern

from ..core.types import Sensitivity


@dataclass(slots=True)
class SensitivityDetector:
    """Regex-based sensitivity classifier."""

    high_patterns: list[Pattern[str]] = field(default_factory=list)
    medium_patterns: list[Pattern[str]] = field(default_factory=list)

    @classmethod
    def default(cls) -> "SensitivityDetector":
        # HIGH: domains where precision is critical
        high = [
            r"\b(iban|tc\s*kimlik|passport|ssn|credit\s*card)\b",
            r"\b(health|diagnosis|medicine|prescription|regl|pregnan)\b",
            r"\b(lawsuit|legal|court|contract|tax)\b",
            r"\b(para|money|usd|try|lira|euro|₺|\$)\b",
        ]
        med = [
            r"\b(address|phone|email)\b",
            r"\b(account|password|login)\b",
        ]
        return cls(
            high_patterns=[re.compile(p, re.IGNORECASE) for p in high],
            medium_patterns=[re.compile(p, re.IGNORECASE) for p in med],
        )

    def detect(self, text: str) -> Sensitivity:
        if not text:
            return Sensitivity.LOW
        for p in self.high_patterns:
            if p.search(text):
                return Sensitivity.HIGH
        for p in self.medium_patterns:
            if p.search(text):
                return Sensitivity.MEDIUM
        return Sensitivity.LOW
