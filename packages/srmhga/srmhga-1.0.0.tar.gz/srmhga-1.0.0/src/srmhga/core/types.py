"""Core data structures for SRM-HGA.

These classes are used across layers, so they are kept lightweight and stable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Dict, Mapping, Optional

from .exceptions import ValidationError
from .utils import normalize_tags, stable_json_dumps, utcnow, sha256_hex


class Policy(str, Enum):
    """Governance policy for a memory record."""

    NORMAL = "NORMAL"
    AUDITABLE = "AUDITABLE"
    USER_CONFIRMED = "USER_CONFIRMED"
    HIGH_STAKES = "HIGH_STAKES"
    PROTECTED = "PROTECTED"

    @property
    def requires_user_confirmation(self) -> bool:
        return self in {Policy.USER_CONFIRMED, Policy.HIGH_STAKES}

    @property
    def is_protected(self) -> bool:
        return self is Policy.PROTECTED


class Sensitivity(str, Enum):
    """Sensitivity level used by UBTP triage."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(slots=True)
class VaultPointer:
    """Pointer into the Deterministic Vault (DV).

    The DV can be implemented with different backends. This pointer is designed
    to be backend-agnostic.

    Parameters
    ----------
    backend:
        Backend identifier (e.g., "sqlite").
    key:
        Backend-specific key/ID.
    namespace:
        Optional namespace prefix (e.g., "facts", "episodes").
    """

    backend: str
    key: str
    namespace: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {"backend": self.backend, "key": self.key, "namespace": self.namespace}



@dataclass(slots=True)
class MemoryMetadata:
    """Metadata stored with every memory item."""

    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)
    last_accessed: Any = field(default_factory=utcnow)

    access_count: int = 0
    tags: list[str] = field(default_factory=list)

    policy: Policy = Policy.NORMAL
    importance: float = 0.0  # in [0,1]
    sensitivity: Sensitivity = Sensitivity.LOW

    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tags = normalize_tags(self.tags)
        if self.access_count < 0:
            raise ValidationError("access_count must be >= 0")
        if not (0.0 <= float(self.importance) <= 1.0):
            raise ValidationError("importance must be in [0,1]")
        if float(self.importance) >= 1.0:
            self.policy = Policy.PROTECTED

    def touch_access(self) -> None:
        """Update access timestamp and counter."""
        self.last_accessed = utcnow()
        self.access_count += 1

    def touch_update(self) -> None:
        """Update updated_at timestamp."""
        self.updated_at = utcnow()

    def add_tags(self, *tags: str) -> None:
        merged = self.tags + list(tags)
        self.tags = normalize_tags(merged)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "last_accessed": str(self.last_accessed),
            "access_count": self.access_count,
            "tags": list(self.tags),
            "policy": self.policy.value,
            "importance": float(self.importance),
            "sensitivity": self.sensitivity.value,
            "extra": dict(self.extra),
        }

    def with_updates(self, **kwargs: Any) -> "MemoryMetadata":
        """Return a copy with provided fields replaced."""
        return replace(self, **kwargs)



@dataclass(slots=True)
class MemoryItem:
    """Lightweight L1 memory item.

    SRM-HGA's L1 (AQSRL) is designed to avoid storing sensitive payloads.
    A MemoryItem typically stores only routing information and metadata.

    Fields
    ------
    id:
        Unique identifier for the item.
    code:
        Vector quantization routing code (centroid id).
    ptr:
        Optional pointer to a deterministic record in the vault.
    meta:
        Memory metadata.
    hash:
        Integrity hash, computed from canonical representation.
    summary:
        Optional short summary/proposition.
    """

    id: str
    code: int
    ptr: Optional[VaultPointer] = None
    meta: MemoryMetadata = field(default_factory=MemoryMetadata)
    summary: Optional[str] = None

    hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValidationError("id must be a non-empty string")
        if not isinstance(self.code, int) or self.code < 0:
            raise ValidationError("code must be a non-negative int")
        self.hash = self.compute_hash()

    def canonical_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": int(self.code),
            "ptr": self.ptr.as_dict() if self.ptr else None,
            "meta": self.meta.as_dict(),
            "summary": self.summary,
        }

    def compute_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.canonical_dict()))

    def verify_integrity(self) -> bool:
        return self.hash == self.compute_hash()

    def with_updates(self, **kwargs: Any) -> "MemoryItem":
        """Return a copy with updates and refreshed hash."""
        item = replace(self, **kwargs)
        # dataclasses.replace does not call __post_init__ for init=False fields
        object.__setattr__(item, "hash", item.compute_hash())
        return item


@dataclass(slots=True)
class SearchHit:
    """Search result item returned by the Deterministic Vault."""

    kind: str
    ref: str
    score: float
    snippet: str
    meta: Dict[str, Any] = field(default_factory=dict)
