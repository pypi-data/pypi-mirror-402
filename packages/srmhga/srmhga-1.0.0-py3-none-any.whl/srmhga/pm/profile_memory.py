"""L3: Profile Memory (PM).

PM stores stable user preferences and constraints. Updates are conservative:
- only write if value changes
- optionally require user confirmation for high-stakes updates
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from ..core.exceptions import UserConfirmationRequired, ValidationError
from ..core.types import Policy, Sensitivity
from ..dv.base import StorageBackend


@dataclass(slots=True)
class ProfileMemory:
    """Profile memory wrapper over the Deterministic Vault."""

    dv: StorageBackend
    confirm_fn: Callable[[str, Any, Any], bool] | None = None
    key_prefix: str = "pm:"  # stored as facts

    def _full_key(self, key: str) -> str:
        if not key:
            raise ValidationError("key must be non-empty")
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Any | None:
        ref = f"fact:{self._full_key(key)}"
        try:
            rec = self.dv.read_exact(ref)
            return rec.get("value")
        except Exception:
            return None

    def set(
        self,
        key: str,
        value: Any,
        *,
        policy: Policy = Policy.USER_CONFIRMED,
        sensitivity: Sensitivity = Sensitivity.MEDIUM,
        provenance: Mapping[str, Any] | None = None,
        require_confirmation: bool | None = None,
    ) -> str:
        """Conservatively set a profile value.

        Returns the stored key (without prefix).
        """
        old = self.get(key)
        if old == value:
            return key

        needs_confirm = policy.requires_user_confirmation or sensitivity is Sensitivity.HIGH
        if require_confirmation is not None:
            needs_confirm = bool(require_confirmation)

        if needs_confirm:
            if self.confirm_fn is None:
                raise UserConfirmationRequired(f"Profile update requires confirmation: {key}")
            if not bool(self.confirm_fn(key, old, value)):
                raise UserConfirmationRequired(f"Profile update denied: {key}")

        self.dv.write_fact(
            self._full_key(key),
            value,
            provenance=provenance or {},
            policy=policy,
            sensitivity=sensitivity,
        )
        return key

    def routing_bias_tags(self) -> list[str]:
        """Return optional tags that can bias semantic routing.

        This is a simple hook; production systems may implement more advanced
        biasing (e.g., centroid re-weighting).
        """
        # MVP: store a special pref 'routing_tags' if present.
        v = self.get("routing_tags")
        if isinstance(v, list):
            return [str(x) for x in v]
        return []
