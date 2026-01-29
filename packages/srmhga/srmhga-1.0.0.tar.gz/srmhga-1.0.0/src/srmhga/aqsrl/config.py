"""AQSRL (L1) configuration.

AQSRL is implemented as a thin wrapper over SRM (Semantic Routing Memory).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AQSRLConfig:
    """Configuration for L1 AQSRL.

    Parameters map closely to the vendored `srm.SRMConfig`.
    """

    K: int = 256
    m: int = 8
    top_k: int = 10
    max_candidates: int = 5000

    pre_normalize: bool = True
    rerank_metric: str = "cosine"  # "cosine" | "dot"

    adaptive_update: bool = False
    tau: float = 0.85
    eta: float = 0.1

    seed: int = 0

    # Bootstrap: how many items to collect before fitting a codebook.
    bootstrap_min_items: int | None = None

    def resolved_bootstrap_min_items(self) -> int:
        base = int(self.bootstrap_min_items or self.K)
        return max(base, self.K)