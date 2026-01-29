"""Deterministic Vault (L2) interfaces.

DV stores exact, structured and auditable records.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Optional, Sequence

from ..core.types import Policy, SearchHit, Sensitivity


class StorageBackend(ABC):
    """Abstract DV storage backend."""

    @abstractmethod
    def write_episodic(self, event: str, meta: Mapping[str, Any] | None = None, *, policy: Policy = Policy.AUDITABLE, sensitivity: Sensitivity = Sensitivity.LOW) -> str:
        """Write an episodic event and return its id."""

    @abstractmethod
    def write_fact(self, key: str, value: Any, provenance: Mapping[str, Any] | None = None, *, policy: Policy = Policy.USER_CONFIRMED, sensitivity: Sensitivity = Sensitivity.MEDIUM) -> str:
        """Write a fact and return its key."""

    @abstractmethod
    def read_exact(self, ref: str) -> Mapping[str, Any]:
        """Read a record by reference."""

    @abstractmethod
    def search(self, query: str, *, limit: int = 20) -> list[SearchHit]:
        """Search across deterministic records."""

    @abstractmethod
    def delete(self, ref: str) -> bool:
        """Delete a record."""

    @abstractmethod
    def load_recent_episodes(self, *, window_seconds: int) -> list[Mapping[str, Any]]:
        """Load recent episodes for consolidation."""
