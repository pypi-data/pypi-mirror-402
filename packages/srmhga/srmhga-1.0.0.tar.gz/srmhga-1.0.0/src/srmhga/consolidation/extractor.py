"""Proposition extraction for consolidation.

In the paper, this may be LLM-based. Here we provide:
- an abstract interface
- a conservative rule-based default implementation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


class PropositionExtractor(ABC):
    @abstractmethod
    def extract(self, episodes: Sequence[Mapping[str, Any]]) -> list[str]:
        """Extract propositions from episodes."""


@dataclass(slots=True)
class RuleBasedPropositionExtractor(PropositionExtractor):
    """A tiny heuristic extractor.

    It strips the episode text and emits short propositions.
    """

    max_props_per_episode: int = 2

    def extract(self, episodes: Sequence[Mapping[str, Any]]) -> list[str]:
        props: list[str] = []
        for ep in episodes:
            text = str(ep.get("event", "")).strip()
            if not text:
                continue
            # Split on sentence-ish boundaries.
            parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
            for p in parts[: self.max_props_per_episode]:
                props.append(p)
        return props
