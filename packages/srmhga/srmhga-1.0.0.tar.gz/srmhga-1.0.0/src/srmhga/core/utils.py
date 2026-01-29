"""Utility helpers used across SRM-HGA.

This module avoids importing heavy optional dependencies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def stable_json_dumps(obj: Any) -> str:
    """Serialize to canonical JSON suitable for hashing.

    - sorted keys
    - compact separators
    - default=str for unknown types
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(data: str) -> str:
    """Compute SHA-256 hex digest for a UTF-8 string."""
    h = hashlib.sha256()
    h.update(data.encode("utf-8"))
    return h.hexdigest()


def normalize_tags(tags: Iterable[str] | None) -> list[str]:
    """Normalize tags (strip, lower, deduplicate preserving order)."""
    if not tags:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for t in tags:
        if t is None:
            continue
        s = str(t).strip().lower()
        if not s:
            continue
        if s in seen:
            continue
        out.append(s)
        seen.add(s)
    return out


def safe_int(value: Any, *, field: str) -> int:
    try:
        return int(value)
    except Exception as e:
        raise ValueError(f"Invalid int for {field}: {value!r}") from e


def ensure_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected mapping for {field}, got {type(value).__name__}")
    return value
