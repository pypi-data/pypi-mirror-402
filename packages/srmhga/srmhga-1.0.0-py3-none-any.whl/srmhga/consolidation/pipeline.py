"""Consolidation pipeline ("sleep phase").

During idle periods, SRM-HGA can consolidate recent deterministic episodes into
semantic propositions in AQSRL, and cautiously update Profile Memory.

This module provides a production-friendly baseline implementation. You can
swap in a stronger PropositionExtractor when connecting to an LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..aqsrl.aqsrl import AQSRL
from ..core.exceptions import ValidationError
from ..core.types import MemoryMetadata, Policy, Sensitivity, VaultPointer
from ..dv.base import StorageBackend
from ..pm.profile_memory import ProfileMemory
from .extractor import PropositionExtractor, RuleBasedPropositionExtractor


@dataclass(slots=True)
class ConsolidationResult:
    episodes_loaded: int
    propositions_written: int


class Consolidator:
    """Consolidate episodes from DV into AQSRL and PM."""

    def __init__(
        self,
        *,
        dv: StorageBackend,
        aqsrl: AQSRL,
        pm: ProfileMemory,
        extractor: PropositionExtractor | None = None,
    ) -> None:
        self.dv = dv
        self.aqsrl = aqsrl
        self.pm = pm
        self.extractor = extractor or RuleBasedPropositionExtractor()

    def consolidate(self, *, window_seconds: int = 3600) -> ConsolidationResult:
        if window_seconds <= 0:
            raise ValidationError("window_seconds must be > 0")

        episodes = self.dv.load_recent_episodes(window_seconds=window_seconds)
        props = self.extractor.extract(episodes)

        n_written = 0
        for ep, prop in zip(episodes, props):
            # Link back to DV episode record
            ptr = VaultPointer(backend="sqlite", namespace="episode", key=str(ep.get("id")))
            meta = MemoryMetadata(policy=Policy.AUDITABLE, sensitivity=Sensitivity.LOW)
            item_id = f"prop:{ep.get('id')}:{n_written}"
            try:
                self.aqsrl.write_semantic(item_id=item_id, text=prop, ptr=ptr, meta=meta, summary=prop)
                n_written += 1
            except Exception:
                # Skip on duplicates or transient routing errors.
                continue

            # Conservative profile update heuristics
            self._maybe_update_profile(prop)

        return ConsolidationResult(episodes_loaded=len(episodes), propositions_written=n_written)

    def _maybe_update_profile(self, proposition: str) -> None:
        text = proposition.lower()
        # Extremely conservative: only update explicit preference statements.
        markers = ["i prefer ", "i like ", "ben sev", "tercih ederim", "i dislike "]
        if not any(m in text for m in markers):
            return
        # Store full proposition under a rolling key for now.
        try:
            self.pm.set(
                "recent_preference",
                proposition,
                policy=Policy.USER_CONFIRMED,
                sensitivity=Sensitivity.MEDIUM,
                provenance={"source": "consolidation", "text": proposition},
                require_confirmation=False,
            )
        except Exception:
            # Ignore if confirmation required or denied.
            return
