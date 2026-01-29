"""Configuration objects.

The :class:`~srmhga.core.config.Config` is intentionally small and stable.
Additional layer-specific configs should live in their respective modules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import ValidationError


@dataclass(slots=True)
class Config:
    """Top-level SRM-HGA configuration.

    Attributes
    ----------
    alpha:
        UBTP confidence threshold. conf(x) >= alpha → eligible for fast semantic path.
    delta_min:
        UBTP margin threshold. margin(x) >= delta_min → eligible for fast semantic path.
    hot_budget_items:
        Soft budget for L1 hot items (used by forgetting logic).
    dv_budget_records:
        Soft budget for DV records (used by forgetting logic).
    slo_read_ms:
        Optional service-level objective for read latency.
    slo_write_ms:
        Optional service-level objective for write latency.
    """

    alpha: float = 0.80
    delta_min: float = 0.05

    hot_budget_items: int = 200_000
    dv_budget_records: int = 1_000_000

    slo_read_ms: float = 50.0
    slo_write_ms: float = 50.0

    def validate(self) -> "Config":
        if not (0.0 <= self.alpha <= 1.0):
            raise ValidationError("alpha must be in [0,1]")
        if self.delta_min < 0:
            raise ValidationError("delta_min must be >= 0")
        if self.hot_budget_items <= 0:
            raise ValidationError("hot_budget_items must be > 0")
        if self.dv_budget_records <= 0:
            raise ValidationError("dv_budget_records must be > 0")
        if self.slo_read_ms <= 0 or self.slo_write_ms <= 0:
            raise ValidationError("SLOs must be > 0")
        return self
