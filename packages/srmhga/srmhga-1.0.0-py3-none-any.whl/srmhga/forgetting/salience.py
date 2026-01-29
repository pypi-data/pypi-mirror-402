"""Salience model for forgetting.

Salience(m) = a * phi(R) + b * psi(F) + g * I

Where:
- R: recency
- F: frequency
- I: importance (governance-weighted)

This is a minimal baseline implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..core.types import MemoryItem


@dataclass(slots=True)
class SalienceWeights:
    a: float = 0.45
    b: float = 0.35
    g: float = 0.20


@dataclass(slots=True)
class SalienceConfig:
    weights: SalienceWeights = field(default_factory=SalienceWeights)
    recency_half_life_seconds: float = 7 * 24 * 3600.0


def _recency_score(last_accessed: str | datetime, *, cfg: SalienceConfig) -> float:
    try:
        dt = last_accessed if isinstance(last_accessed, datetime) else datetime.fromisoformat(str(last_accessed))
        age = (datetime.now(dt.tzinfo) - dt).total_seconds()
        hl = max(1.0, float(cfg.recency_half_life_seconds))
        # Exponential decay, normalized to (0,1]
        return float(0.5 ** (age / hl))
    except Exception:
        return 0.0


def _freq_score(access_count: int) -> float:
    # Log-like compression
    from math import log1p

    try:
        return float(min(1.0, log1p(max(0, int(access_count))) / 5.0))
    except Exception:
        return 0.0


def salience(item: MemoryItem, *, cfg: SalienceConfig) -> float:
    """Compute salience in [0,1] (best-effort)."""
    R = _recency_score(item.meta.last_accessed, cfg=cfg)
    F = _freq_score(item.meta.access_count)
    I = float(max(0.0, min(1.0, item.meta.importance)))
    w = cfg.weights
    s = w.a * R + w.b * F + w.g * I
    return float(max(0.0, min(1.0, s)))
