"""Salience-guided forgetting.

This module enforces size budgets by applying simple guardrailed actions.

Actions in the paper:
- Keep
- Summarize
- Migrate
- Delete

In this baseline, only **Keep** and **Delete** are implemented. Summarize and
Migrate are exposed as extension points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Optional

from ..aqsrl.aqsrl import AQSRL
from ..core.types import MemoryItem, Policy
from .salience import SalienceConfig, salience


class ForgetAction(str, Enum):
    KEEP = "KEEP"
    SUMMARIZE = "SUMMARIZE"
    MIGRATE = "MIGRATE"
    DELETE = "DELETE"


@dataclass(slots=True)
class ForgetResult:
    before: int
    after: int
    deleted: int


@dataclass(slots=True)
class ForgetConfig:
    salience: SalienceConfig = field(default_factory=SalienceConfig)


def forget_l1(aqsrl: AQSRL, *, budget_hot: int, cfg: ForgetConfig | None = None) -> ForgetResult:
    """Enforce L1 budget by deleting lowest-salience unprotected items."""
    cfg = cfg or ForgetConfig()
    budget_hot = max(0, int(budget_hot))
    before = aqsrl.size
    if budget_hot <= 0:
        return ForgetResult(before=before, after=before, deleted=0)
    if before <= budget_hot:
        return ForgetResult(before=before, after=before, deleted=0)

    # AQSRL hides registry; export items via internal snapshot.
    items: list[MemoryItem] = list(aqsrl._items.values())  # type: ignore[attr-defined]
    # Compute salience and sort ascending
    scored = []
    for it in items:
        if it.meta.policy is Policy.PROTECTED or it.meta.importance >= 1.0:
            continue
        scored.append((salience(it, cfg=cfg.salience), it.id))

    scored.sort(key=lambda t: t[0])
    to_delete = max(0, before - budget_hot)
    deleted = 0
    for _, item_id in scored[:to_delete]:
        if aqsrl.delete(item_id):
            deleted += 1

    after = aqsrl.size
    return ForgetResult(before=before, after=after, deleted=deleted)
